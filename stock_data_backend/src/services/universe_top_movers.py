from __future__ import annotations

import os
from typing import List, Tuple

from src.api.schemas import AnalyzeGrowthRequest, GrowthResult, PriceField
from src.services.finance_client import FinanceClient
from src.services.growth_analyzer import analyze_growth


SYMBOLS_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "symbols")


def _read_symbol_file(fname: str) -> List[str]:
    path = os.path.abspath(os.path.join(SYMBOLS_BASE, fname))
    if not os.path.exists(path):
        return []
    symbols: List[str] = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                symbols.append(s)
    # de-duplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for s in symbols:
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    return ordered


def get_universe_symbols(universe: str) -> List[str]:
    """Return a list of symbols for the given universe name.

    Currently supports:
    - 'NASDAQ' (or 'NASDAQ_100') via nasdaq_100.txt
    - 'SP500' (or 'S&P_500') via sp500.txt
    """
    uni = (universe or "NASDAQ").strip().upper()
    # NASDAQ 100
    if uni in {"NASDAQ", "NASDAQ_100"}:
        syms = _read_symbol_file("nasdaq_100.txt")
        if syms:
            return syms
    # S&P 500
    if uni in {"SP500", "S&P_500", "S&P500"}:
        syms = _read_symbol_file("sp500.txt")
        if syms:
            return syms
    # Fallback: empty list
    return []


# PUBLIC_INTERFACE
def get_top_movers_universe(
    universe: str,
    start_date,
    end_date,
    limit: int,
    price_field: PriceField | None,
    client: FinanceClient,
) -> Tuple[List[GrowthResult], List[str]]:
    """Compute top movers within a universe by growth percentage.

    This reuses the existing analyze_growth path by constructing a request with the universe's symbols.
    """
    symbols = get_universe_symbols(universe)
    # Short-circuit if we have no symbols
    if not symbols:
        return [], [f"No symbols found for universe '{universe}'"]

    # Build a temporary request that uses the same computation path for per-ticker growth
    temp_req = AnalyzeGrowthRequest(
        tickers=symbols,
        start_date=start_date,
        end_date=end_date,
        min_growth_pct=None,
        max_growth_pct=None,
        limit=max(limit, 1),  # ensure positive
        price_field=price_field or PriceField.close,
        universe=universe,
    )
    results, warnings = analyze_growth(temp_req, client)
    return results, warnings
