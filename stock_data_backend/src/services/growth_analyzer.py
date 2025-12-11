from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from src.api.schemas import AnalyzeGrowthRequest, GrowthResult, PriceField
from src.services.finance_client import FinanceClient, PriceBar


@dataclass
class SeriesSelection:
    """Selected start and end points within the available bars."""
    start_idx: Optional[int]
    end_idx: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    start_price: Optional[float]
    end_price: Optional[float]
    count: int
    warning: Optional[str]


def _select_price(bar: PriceBar, field: PriceField) -> Optional[float]:
    if field == PriceField.adj_close:
        return bar.adj_close
    if field == PriceField.open:
        return bar.open
    # default close
    return bar.close


def _pick_endpoints(bars: List[PriceBar], field: PriceField) -> SeriesSelection:
    if not bars:
        return SeriesSelection(None, None, None, None, None, None, 0, "No data within date range")
    # Choose first available as start, last available as end
    start_idx = 0
    end_idx = len(bars) - 1
    # Resolve prices, skipping None values if needed towards nearest available
    # start
    s_idx = start_idx
    s_price = _select_price(bars[s_idx], field)
    while s_idx <= end_idx and s_price is None:
        s_idx += 1
        if s_idx <= end_idx:
            s_price = _select_price(bars[s_idx], field)
    # end
    e_idx = end_idx
    e_price = _select_price(bars[e_idx], field)
    while e_idx >= s_idx and e_price is None:
        e_idx -= 1
        if e_idx >= s_idx:
            e_price = _select_price(bars[e_idx], field)
    if s_price is None or e_price is None or s_idx > e_idx:
        return SeriesSelection(None, None, None, None, None, None, len(bars), "Missing valid prices within range")
    return SeriesSelection(
        start_idx=s_idx,
        end_idx=e_idx,
        start_date=bars[s_idx].date,
        end_date=bars[e_idx].date,
        start_price=s_price,
        end_price=e_price,
        count=len(bars),
        warning=None,
    )


# PUBLIC_INTERFACE
def analyze_growth(req: AnalyzeGrowthRequest, client: FinanceClient) -> Tuple[List[GrowthResult], List[str]]:
    """Compute growth results for the given request using provided finance client.

    Returns tuple of (results, global_warnings).
    """
    results: List[GrowthResult] = []
    global_warnings: List[str] = []

    for raw_ticker in req.tickers:
        ticker = raw_ticker.strip()
        if not ticker:
            continue

        try:
            provider_symbol = client.symbol_for_provider(ticker)
            bars = client.get_daily_bars(provider_symbol, req.start_date, req.end_date)
        except Exception as e:
            warning = f"{ticker}: fetch error - {e}"
            global_warnings.append(warning)
            results.append(
                GrowthResult(
                    ticker=ticker,
                    provider_symbol=provider_symbol if 'provider_symbol' in locals() else ticker,
                    points_count=0,
                    warning="Fetch error",
                )
            )
            continue

        selection = _pick_endpoints(bars, req.price_field or PriceField.close)
        if selection.start_price is None or selection.end_price is None:
            warn = selection.warning or "Insufficient data"
            results.append(
                GrowthResult(
                    ticker=ticker,
                    provider_symbol=provider_symbol,
                    start_date_effective=selection.start_date,
                    end_date_effective=selection.end_date,
                    start_price=selection.start_price,
                    end_price=selection.end_price,
                    growth_pct=None,
                    abs_return=None,
                    points_count=selection.count,
                    warning=warn,
                )
            )
            global_warnings.append(f"{ticker}: {warn}")
            continue

        start_p = selection.start_price
        end_p = selection.end_price
        growth_pct = None
        abs_return = None
        if start_p is not None and start_p != 0 and end_p is not None:
            abs_return = end_p - start_p
            growth_pct = (abs_return / start_p) * 100.0

        results.append(
            GrowthResult(
                ticker=ticker,
                provider_symbol=provider_symbol,
                start_date_effective=selection.start_date,
                end_date_effective=selection.end_date,
                start_price=start_p,
                end_price=end_p,
                growth_pct=growth_pct,
                abs_return=abs_return,
                points_count=selection.count,
                warning=None,
            )
        )

    # Filter by growth range if provided; only keep items with a computed growth
    filtered: List[GrowthResult] = []
    for r in results:
        if r.growth_pct is None:
            continue
        if req.min_growth_pct is not None and r.growth_pct < req.min_growth_pct:
            continue
        if req.max_growth_pct is not None and r.growth_pct > req.max_growth_pct:
            continue
        filtered.append(r)

    # Sort by growth_pct desc
    filtered.sort(key=lambda x: (x.growth_pct if x.growth_pct is not None else float("-inf")), reverse=True)

    # Apply limit
    limited = filtered[: req.limit]

    return limited, global_warnings
