from typing import Dict

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.api.schemas import AnalyzeGrowthRequest, AnalyzeGrowthResponse, PriceField
from src.config import settings
from src.services.finance_client import get_finance_client
from src.services.growth_analyzer import analyze_growth
from src.services.universe_top_movers import get_top_movers_universe

app = FastAPI(
    title="Stock Growth Analyzer API",
    description="Backend service that fetches historical stock prices and computes growth over a date range.",
    version="0.1.0",
    openapi_tags=[
        {"name": "Health", "description": "Health and diagnostics"},
        {"name": "Providers", "description": "Provider information"},
        {"name": "Analysis", "description": "Growth analysis operations"},
    ],
)

# Configure CORS using env settings
origins = settings.allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"], summary="Health Check", description="Simple healthcheck endpoint for service monitoring.")
def health_check():
    """Health check endpoint that returns a simple JSON object."""
    return {"message": "Healthy"}


@app.get(
    "/providers",
    tags=["Providers"],
    summary="List available data providers",
    description="Return the active finance data provider and any optional notes.",
)
def get_providers() -> Dict[str, str]:
    """Return active provider info determined by environment configuration."""
    provider = settings.FINANCE_API_PROVIDER or "stooq"
    notes = "Default provider (no API key required)" if provider == "stooq" else "Requires API key"
    return {"active_provider": provider, "notes": notes}


@app.post(
    "/analyze-growth",
    tags=["Analysis"],
    summary="Analyze stock growth for tickers over a date range",
    description=(
        "Given one or more stock tickers and a date range, fetch the time series, "
        "select start and end prices within the range for the selected price field, compute growth percentage "
        "and absolute return, apply optional growth filters, sort by growth desc, and return the top results."
        "\n\nNotes:\n"
        "- Default provider is Stooq. Symbols are mapped to lowercase with '.us' suffix (e.g., AAPL -> aapl.us).\n"
        "- Alpha Vantage can be used by setting FINANCE_API_PROVIDER=alpha_vantage and FINANCE_API_KEY.\n"
        "- If 'tickers' is omitted or empty, the endpoint returns the top N movers within the specified 'universe' (default: NASDAQ; also supports 'SP500' for S&P 500), using 'limit' (default: 10)."
    ),
    response_model=AnalyzeGrowthResponse,
    responses={
        200: {"description": "Computed growth results."},
        422: {"description": "Validation error."},
        500: {"description": "Server error while fetching or processing data."},
    },
)
def analyze_growth_endpoint(payload: AnalyzeGrowthRequest = Body(...)) -> AnalyzeGrowthResponse:
    """Compute and return growth analysis results.

    Parameters:
    - payload: AnalyzeGrowthRequest containing optional tickers, start_date, end_date, optional growth filters,
      result limit, price field, and optional universe for empty-ticker screening.

    Behavior:
    - When 'tickers' is provided and non-empty: compute growth for those tickers.
    - When 'tickers' is omitted or empty: compute top N movers within the selected universe (default: NASDAQ).

    Returns:
    - AnalyzeGrowthResponse with results and warnings.
    """
    try:
        client = get_finance_client()
        # If tickers are provided and non-empty, use existing path
        if payload.tickers and len(payload.tickers) > 0:
            results, warnings = analyze_growth(payload, client)
            return AnalyzeGrowthResponse(results=results, warnings=warnings)

        # Universe screening path
        uni = payload.universe or "NASDAQ"
        pf = payload.price_field or PriceField.close
        results, warnings = get_top_movers_universe(
            universe=uni,
            start_date=payload.start_date,
            end_date=payload.end_date,
            limit=payload.limit or 10,
            price_field=pf,
            client=client,
        )
        return AnalyzeGrowthResponse(results=results, warnings=warnings)
    except HTTPException:
        raise
    except Exception as e:
        # Generic error handling
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal error: {e}"},
        )
