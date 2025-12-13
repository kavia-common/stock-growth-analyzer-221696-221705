import os
from typing import Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load environment variables from .env if present (without hardcoding path).
# Users should ensure a .env file is present in this directory with necessary variables.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # If python-dotenv is not installed, the app should still run using process env
    pass


# PUBLIC_INTERFACE
class HealthResponse(BaseModel):
    """Response model for service health check."""
    status: str = Field(..., description="Service health status string (e.g., 'ok').")
    service: str = Field(..., description="Name of the service reporting health.")
    version: str = Field(..., description="Application version string.")
    env: str = Field(..., description="Deployment environment label.")


APP_NAME = os.getenv("APP_NAME", "stock_data_backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENV = os.getenv("APP_ENV", "development")

app = FastAPI(
    title="Stock Data Backend API",
    description="FastAPI service providing stock growth analytics and data endpoints.",
    version=APP_VERSION,
    openapi_tags=[
        {"name": "Health", "description": "Service readiness and liveness probes."},
    ],
)

# Allow CORS from all origins by default; override via env if needed
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins.split(",")] if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Service health check",
    description="Returns health status for readiness/liveness probes.",
    responses={
        200: {"description": "Service is healthy", "model": HealthResponse},
        503: {"description": "Service is not healthy"},
    },
)
def health() -> HealthResponse:
    """Health endpoint indicating service is up and responding."""
    return HealthResponse(status="ok", service=APP_NAME, version=APP_VERSION, env=APP_ENV)

# PUBLIC_INTERFACE
@app.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="API health check (alias)",
    description="Alias health endpoint under /api.",
    responses={
        200: {"description": "Service is healthy", "model": HealthResponse},
        503: {"description": "Service is not healthy"},
    },
)
def api_health() -> HealthResponse:
    """Alias health endpoint under /api for some proxy configurations."""
    return HealthResponse(status="ok", service=APP_NAME, version=APP_VERSION, env=APP_ENV)


def get_uvicorn_host_port() -> Dict[str, str]:
    """Resolve host and port from environment variables with sensible defaults."""
    host = os.getenv("HOST", "0.0.0.0")
    # Default port 3001 as requested
    port_str = os.getenv("PORT", "3001")
    # Sanitize port in case of malformed input
    try:
        int(port_str)
    except ValueError:
        port_str = "3001"
    return {"host": host, "port": port_str}


if __name__ == "__main__":
    # Running via `python -m app.main` or `python app/main.py`
    # Prefer uvicorn import to avoid a shell dependency
    import uvicorn

    hp = get_uvicorn_host_port()
    uvicorn.run(
        "app.main:app",
        host=hp["host"],
        port=int(hp["port"]),
        reload=bool(os.getenv("UVICORN_RELOAD", "false").lower() in ["1", "true", "yes"]),
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
