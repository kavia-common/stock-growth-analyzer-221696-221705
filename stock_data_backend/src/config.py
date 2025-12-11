import os
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    def __init__(self) -> None:
        # Finance provider: 'stooq' (default) or 'alpha_vantage'
        self.FINANCE_API_PROVIDER: str = os.getenv("FINANCE_API_PROVIDER", "stooq").strip().lower()

        # Optional API key for providers that need it (e.g., Alpha Vantage)
        self.FINANCE_API_KEY: Optional[str] = os.getenv("FINANCE_API_KEY") or None

        # Optional base URL override for finance API. If not provided, sensible defaults per provider are used.
        self.FINANCE_API_BASE_URL: Optional[str] = os.getenv("FINANCE_API_BASE_URL") or None

        # Allowed origins for CORS. Comma separated list, default '*'
        self.ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "*").strip()

    # PUBLIC_INTERFACE
    def allowed_origins(self) -> List[str]:
        """Return the list of origins allowed for CORS."""
        raw = self.ALLOWED_ORIGINS_RAW
        if raw == "*":
            return ["*"]
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return parts or ["*"]


settings = Settings()
