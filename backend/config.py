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

# Comma-separated paths to scan, e.g. /mnt/Media,/mnt/Movies
# Leave empty to scan all datasets (slow on large NAS)
SCAN_PATHS: list = [p.strip() for p in os.getenv("SCAN_PATHS", "").split(",") if p.strip()]

# Max concurrent TrueNAS API requests during directory traversal
NAS_CONCURRENCY: int = int(os.getenv("NAS_CONCURRENCY", "20"))

# How many hours disk cache is considered fresh (0 = always refetch)
CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "24"))
