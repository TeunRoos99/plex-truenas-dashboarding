from datetime import datetime, timedelta, timezone
from typing import Any
from config import STALE_MONTHS


def shows_overview(plex_items: list) -> list:
    """Per serie: totaal afleveringen, hoeveel bekeken, laatste kijkdatum, toegevoegd."""
    shows: dict = {}

    for item in plex_items:
        if item.get("type") != "episode":
            continue

        title = item.get("show_title") or "Onbekend"
        if title not in shows:
            shows[title] = {
                "show_title": title,
                "total_episodes": 0,
                "watched_episodes": 0,
                "total_size": 0,
                "last_viewed_at": None,
                "added_at": None,
            }

        s = shows[title]
        s["total_episodes"] += 1
        s["total_size"] += item.get("file_size", 0)
        if item.get("view_count", 0) > 0:
            s["watched_episodes"] += 1

        lv = item.get("last_viewed_at")
        if lv and (s["last_viewed_at"] is None or lv > s["last_viewed_at"]):
            s["last_viewed_at"] = lv

        ad = item.get("added_at")
        if ad and (s["added_at"] is None or ad < s["added_at"]):
            s["added_at"] = ad

    result = list(shows.values())
    for s in result:
        t = s["total_episodes"]
        s["watched_pct"] = round(s["watched_episodes"] / t * 100) if t else 0

    return sorted(result, key=lambda x: x["show_title"].lower())


def never_watched(plex_items: list) -> list:
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
