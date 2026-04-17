from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")

TRUENAS_URL: str = os.getenv("TRUENAS_URL", "")
TRUENAS_API_KEY: str = os.getenv("TRUENAS_API_KEY", "")
TRUENAS_VERIFY_SSL: bool = os.getenv("TRUENAS_VERIFY_SSL", "false").lower() == "true"

PLEX_URL: str = os.getenv("PLEX_URL", "http://localhost:32400")
PLEX_TOKEN: str = os.getenv("PLEX_TOKEN", "")

STALE_MONTHS: int = int(os.getenv("STALE_MONTHS", "6"))
