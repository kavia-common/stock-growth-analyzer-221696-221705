from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class PriceField(str, Enum):
    """Supported price fields for growth calculation."""
    close = "close"
    adj_close = "adj_close"
    open = "open"


class AnalyzeGrowthRequest(BaseModel):
    """Request payload for growth analysis."""
    tickers: List[str] = Field(..., description="List of stock tickers to analyze (e.g., ['AAPL','MSFT']).")
    start_date: date = Field(..., description="Start date for analysis (YYYY-MM-DD).")
    end_date: date = Field(..., description="End date for analysis (YYYY-MM-DD).")
    min_growth_pct: Optional[float] = Field(None, description="Optional minimum growth percentage filter (e.g., 5 means >=5%).")
    max_growth_pct: Optional[float] = Field(None, description="Optional maximum growth percentage filter (e.g., 50 means <=50%).")
    limit: int = Field(10, description="Maximum number of results to return, sorted by growth percentage desc.")
    price_field: Optional[PriceField] = Field(PriceField.close, description="Which price field to use for growth calculation.")

    @model_validator(mode="after")
    def validate_dates_and_tickers(self):
        if not self.tickers or len([t for t in self.tickers if t and t.strip()]) == 0:
            raise ValueError("tickers must be a non-empty list of symbols.")
        if self.start_date > self.end_date:
            raise ValueError("start_date must be less than or equal to end_date.")
        if self.limit <= 0:
            raise ValueError("limit must be a positive integer.")
        if self.min_growth_pct is not None and self.max_growth_pct is not None:
            if self.min_growth_pct > self.max_growth_pct:
                raise ValueError("min_growth_pct cannot be greater than max_growth_pct.")
        return self


class GrowthResult(BaseModel):
    """A single ticker's growth result."""
    ticker: str = Field(..., description="Input ticker symbol as provided in the request.")
    provider_symbol: str = Field(..., description="The symbol used for provider fetch (e.g., aapl.us for Stooq).")
    start_date_effective: Optional[date] = Field(None, description="The date of the first data point used within the range.")
    end_date_effective: Optional[date] = Field(None, description="The date of the last data point used within the range.")
    start_price: Optional[float] = Field(None, description="Price at start_date_effective for the selected price_field.")
    end_price: Optional[float] = Field(None, description="Price at end_date_effective for the selected price_field.")
    growth_pct: Optional[float] = Field(None, description="Percentage growth between start and end prices.")
    abs_return: Optional[float] = Field(None, description="Absolute return (end_price - start_price).")
    points_count: int = Field(0, description="Number of data points available in the period.")
    warning: Optional[str] = Field(None, description="Warning message if data was missing or insufficient.")


class AnalyzeGrowthResponse(BaseModel):
    """Response payload for growth analysis containing results and optional warnings."""
    results: List[GrowthResult] = Field(..., description="Sorted results, by growth_pct desc.")
    warnings: List[str] = Field(default_factory=list, description="Global warnings encountered during processing.")
