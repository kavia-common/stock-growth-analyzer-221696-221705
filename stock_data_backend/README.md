# stock_data_backend

FastAPI backend service for stock growth analytics.

## Features (initial scaffolding)
- Health endpoints:
  - GET /health
  - GET /api/health
- OpenAPI docs at /docs and /openapi.json
- CORS enabled (configure via ALLOWED_ORIGINS)

## Getting started
1. Create and populate a `.env` file in this directory (optional):
   ```
   APP_NAME=stock_data_backend
   APP_VERSION=0.1.0
   APP_ENV=development
   HOST=0.0.0.0
   PORT=3001
   ALLOWED_ORIGINS=*
   LOG_LEVEL=info
   UVICORN_RELOAD=false
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   python -m app.main
   ```
4. Verify health:
   - http://localhost:3001/health
   - http://localhost:3001/api/health

## Notes
- Do not hardcode secrets; use environment variables via the `.env` file.
- This is a minimal scaffold to allow the frontend to detect backend readiness.
