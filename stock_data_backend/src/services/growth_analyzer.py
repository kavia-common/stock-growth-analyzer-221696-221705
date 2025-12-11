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


def _pick_endpoints(bars: List[PriceBar], field: PriceField, start_target: date | None = None, end_target: date | None = None) -> SeriesSelection:
    """
    Choose nearest endpoints around requested range:
    - start: first bar on/after start_target; fallback to latest bar before start if needed
    - end: last bar on/before end_target; fallback to earliest bar after end if needed
    Also skip None prices by moving inward toward nearest available values.
    """
    if not bars:
        return SeriesSelection(None, None, None, None, None, None, 0, "No data available for symbol")

    n = len(bars)

    # Helper to find index of first date >= target; else -1
    def first_on_or_after(target: date) -> int:
        lo, hi = 0, n - 1
        ans = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if bars[mid].date >= target:
                ans = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return ans

    # Helper to find index of last date <= target; else -1
    def last_on_or_before(target: date) -> int:
        lo, hi = 0, n - 1
        ans = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if bars[mid].date <= target:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return ans

    # Initial indices based on targets when provided
    s_idx = 0
    e_idx = n - 1

    if start_target is not None:
        idx = first_on_or_after(start_target)
        if idx == -1:
            # No data on/after start; fallback to last before start
            idx = last_on_or_before(start_target)
        if idx != -1:
            s_idx = idx

    if end_target is not None:
        idx = last_on_or_before(end_target)
        if idx == -1:
            # No data on/before end; fallback to first after end
            idx = first_on_or_after(end_target)
        if idx != -1:
            e_idx = idx

    if s_idx > e_idx:
        return SeriesSelection(None, None, None, None, None, None, n, "No overlapping data near requested dates")

    # Move s_idx forward until selected price is available
    s_price = _select_price(bars[s_idx], field)
    while s_idx <= e_idx and s_price is None:
        s_idx += 1
        if s_idx <= e_idx:
            s_price = _select_price(bars[s_idx], field)

    # Move e_idx backward until selected price is available
    e_price = _select_price(bars[e_idx], field)
    while e_idx >= s_idx and e_price is None:
        e_idx -= 1
        if e_idx >= s_idx:
            e_price = _select_price(bars[e_idx], field)

    if s_price is None or e_price is None or s_idx > e_idx:
        return SeriesSelection(None, None, None, None, None, None, n, "Missing valid prices near requested dates")

    return SeriesSelection(
        start_idx=s_idx,
        end_idx=e_idx,
        start_date=bars[s_idx].date,
        end_date=bars[e_idx].date,
        start_price=s_price,
        end_price=e_price,
        count=n,
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

        selection = _pick_endpoints(
            bars,
            req.price_field or PriceField.close,
            start_target=req.start_date,
            end_target=req.end_date,
        )
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

    # If this request originated from universe mode (tickers length large) and nothing survived,
    # add a clear global warning to guide the user.
    if len(req.tickers or []) > 0 and len(limited) == 0:
        global_warnings.append(
            "No results after snapping to nearest trading days. This often occurs when the chosen date range "
            "does not include trading days (e.g., weekends/holidays) or when the provider lacks coverage for many symbols. "
            "Try adjusting dates to business days or expanding the range/universe."
        )

    return limited, global_warnings
