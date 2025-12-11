# stock-growth-analyzer-221696-221705

Backend: Stock Data Backend (FastAPI)
-------------------------------------

This backend provides endpoints to analyze stock growth over a date range by fetching historical prices from a finance data provider (default: Stooq). Optionally, Alpha Vantage can be used.

Endpoints:
- GET / — Health check
- GET /providers — Returns the active provider info
- POST /analyze-growth — Computes growth for provided tickers

Environment variables (see stock_data_backend/.env.example):
- FINANCE_API_PROVIDER: stooq (default) or alpha_vantage
- FINANCE_API_KEY: required for alpha_vantage
- FINANCE_API_BASE_URL: optional override for provider API base URL
- ALLOWED_ORIGINS: CSV list of origins allowed by CORS (e.g., http://localhost:3000)

Stooq symbol mapping:
- For common US tickers, the backend maps AAPL -> aapl.us, MSFT -> msft.us, etc.
- Not all instruments are available on Stooq; expect warnings for missing data.

Local development
1. cd stock_data_backend
2. Create .env from example:
   cp .env.example .env
   # Adjust variables as needed
3. Create virtualenv and install requirements (if not handled by the environment):
   pip install -r requirements.txt
4. Run the API:
   uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

OpenAPI schema
- Generate openapi.json (writes into stock_data_backend/interfaces/openapi.json):
  python -m src.api.generate_openapi

Example request body for /analyze-growth:
{
  "tickers": ["AAPL", "MSFT"],
  "start_date": "2024-01-02",
  "end_date": "2024-03-29",
  "min_growth_pct": 0,
  "max_growth_pct": 1000,
  "limit": 10,
  "price_field": "close"
}