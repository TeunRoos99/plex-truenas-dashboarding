from datetime import datetime, timedelta, timezone
from typing import Any
from config import STALE_MONTHS


def never_watched(plex_items: list[dict]) -> list[dict]:
    return [item for item in plex_items if not item.get("view_count")]


def stale_items(plex_items: list[dict]) -> list[dict]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30 * STALE_MONTHS)
    result = []
    for item in plex_items:
        lv = item.get("last_viewed_at")
        if lv is None:
            continue  # never watched — covered by never_watched
        last_viewed = datetime.fromisoformat(lv)
        if last_viewed < cutoff:
            result.append(item)
    return result


def orphaned_files(
    nas_files: list[dict], plex_items: list[dict]
) -> list[dict[str, Any]]:
    """Files on NAS that are not referenced by any Plex item."""
    plex_paths: set[str] = set()
    for item in plex_items:
        for fp in item.get("file_paths", []):
            plex_paths.add(_normalize(fp))

    MEDIA_EXTENSIONS = {
        ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v",
        ".ts", ".flv", ".webm", ".mpg", ".mpeg",
    }

    orphans = []
    for f in nas_files:
        path = f.get("path", "")
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext not in MEDIA_EXTENSIONS:
            continue
        if _normalize(path) not in plex_paths:
            orphans.append(f)
    return orphans


def summary(
    nas_files: list[dict],
    plex_items: list[dict],
    orphans: list[dict],
    never: list[dict],
    stale: list[dict],
) -> dict[str, Any]:
    total_size = sum(f.get("size", 0) for f in nas_files)
    return {
        "total_nas_files": len(nas_files),
        "total_nas_size_bytes": total_size,
        "total_nas_size_gb": round(total_size / (1024**3), 2),
        "total_plex_items": len(plex_items),
        "never_watched_count": len(never),
        "stale_count": len(stale),
        "orphaned_count": len(orphans),
    }


def _normalize(path: str) -> str:
    return path.strip().lower().rstrip("/")
