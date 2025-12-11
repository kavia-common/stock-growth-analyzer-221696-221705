import csv
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
from typing import Dict, Iterable, List, Optional

import httpx

from src.config import settings


@dataclass
class PriceBar:
    """Represents a single OHLCV bar for a day."""
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    adj_close: Optional[float]
    volume: Optional[int]


class FinanceClient:
    """Abstract interface for fetching historical daily bars for a ticker."""

    # PUBLIC_INTERFACE
    def symbol_for_provider(self, ticker: str) -> str:
        """Map a user-provided ticker to the provider-specific symbol."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def get_daily_bars(
        self, symbol: str, start: date, end: date
    ) -> List[PriceBar]:
        """Fetch daily historical bars for a symbol in [start, end] inclusive."""
        raise NotImplementedError


class StooqClient(FinanceClient):
    """Fetch historical daily data from Stooq in CSV format.

    Notes:
    - Stooq symbols for US equities typically end with '.us', in lowercase.
      Example: 'AAPL' -> 'aapl.us'
    - The dataset includes columns: Date, Open, High, Low, Close, Volume
      'Adj Close' is not always present; when absent we reuse 'Close'.
    - No API key is required.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or "https://stooq.com/q/d/l/?s={symbol}&i=d"

    def symbol_for_provider(self, ticker: str) -> str:
        return f"{ticker.strip().lower()}.us"

    def get_daily_bars(self, symbol: str, start: date, end: date) -> List[PriceBar]:
        url = self.base_url.format(symbol=symbol)
        # Sequential sync call is fine.
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url)
            r.raise_for_status()
            text = r.text

        # Parse CSV
        bars: List[PriceBar] = []
        f = StringIO(text)
        reader = csv.DictReader(f)
        # Normalize headers
        headers = [h.strip().lower() for h in reader.fieldnames or []]
        has_adj = "adj close" in headers or "adj_close" in headers or "adjclose" in headers
        # Iterate rows
        for row in reader:
            try:
                d_str = row.get("Date") or row.get("date")
                if not d_str:
                    continue
                d = datetime.strptime(d_str, "%Y-%m-%d").date()
                if d < start or d > end:
                    # We could read all and filter by date range as requested.
                    continue
                def to_float(key_variants: Iterable[str]) -> Optional[float]:
                    for k in key_variants:
                        v = row.get(k)
                        if v is None or v == "":
                            continue
                        try:
                            return float(v)
                        except Exception:
                            continue
                    return None

                o = to_float(["Open", "open"])
                h = to_float(["High", "high"])
                l = to_float(["Low", "low"])
                c = to_float(["Close", "close"])
                ac = to_float(["Adj Close", "adj close", "adj_close", "AdjClose"]) if has_adj else c
                vol_str = row.get("Volume") or row.get("volume")
                vol = None
                if vol_str:
                    try:
                        vol = int(vol_str.replace(",", ""))
                    except Exception:
                        vol = None

                bars.append(PriceBar(date=d, open=o, high=h, low=l, close=c, adj_close=ac, volume=vol))
            except Exception:
                # skip malformed rows
                continue

        # Ensure sorted by date
        bars.sort(key=lambda b: b.date)
        return bars


class AlphaVantageClient(FinanceClient):
    """Fetch historical daily adjusted data from Alpha Vantage.

    Requires FINANCE_API_KEY in environment when selected.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.base_url = base_url or "https://www.alphavantage.co/query"
        self.api_key = api_key or settings.FINANCE_API_KEY

    def symbol_for_provider(self, ticker: str) -> str:
        # Alpha Vantage typically uses raw symbols like 'AAPL'
        return ticker.strip().upper()

    def get_daily_bars(self, symbol: str, start: date, end: date) -> List[PriceBar]:
        if not self.api_key:
            raise ValueError("Alpha Vantage requires FINANCE_API_KEY environment variable.")

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": self.api_key,
        }

        with httpx.Client(timeout=20.0) as client:
            r = client.get(self.base_url, params=params)
            r.raise_for_status()
            data = r.json()

        key = "Time Series (Daily)"
        if key not in data:
            # Error message pass-through if present
            raise ValueError(f"Alpha Vantage error or unexpected response: {data.get('Note') or data.get('Error Message') or 'unknown'}")

        ts: Dict[str, Dict[str, str]] = data[key]
        bars: List[PriceBar] = []
        for d_str, values in ts.items():
            try:
                d = datetime.strptime(d_str, "%Y-%m-%d").date()
                if d < start or d > end:
                    continue
                o = float(values.get("1. open")) if values.get("1. open") else None
                h = float(values.get("2. high")) if values.get("2. high") else None
                l = float(values.get("3. low")) if values.get("3. low") else None
                c = float(values.get("4. close")) if values.get("4. close") else None
                ac = float(values.get("5. adjusted close")) if values.get("5. adjusted close") else c
                vol = int(values.get("6. volume")) if values.get("6. volume") else None
                bars.append(PriceBar(date=d, open=o, high=h, low=l, close=c, adj_close=ac, volume=vol))
            except Exception:
                continue

        bars.sort(key=lambda b: b.date)
        return bars


# PUBLIC_INTERFACE
def get_finance_client() -> FinanceClient:
    """Factory to return a finance client based on FINANCE_API_PROVIDER env."""
    provider = (settings.FINANCE_API_PROVIDER or "stooq").lower()
    base_url = settings.FINANCE_API_BASE_URL or None
    if provider == "alpha_vantage":
        return AlphaVantageClient(base_url=base_url, api_key=settings.FINANCE_API_KEY)
    # default to Stooq
    return StooqClient(base_url=base_url)
