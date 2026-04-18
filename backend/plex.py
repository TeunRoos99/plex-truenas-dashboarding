import httpx
from datetime import datetime, timezone
from typing import Any, Optional
from config import PLEX_URL, PLEX_TOKEN


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=PLEX_URL.rstrip("/"),
        headers={"X-Plex-Token": PLEX_TOKEN, "Accept": "application/json"},
        timeout=60,
    )


def get_libraries() -> list[dict[str, Any]]:
    with _client() as client:
        resp = client.get("/library/sections")
        resp.raise_for_status()
        sections = resp.json()["MediaContainer"].get("Directory", [])
    return [
        {"key": s["key"], "title": s["title"], "type": s["type"]}
        for s in sections
        if s["type"] in ("movie", "show")
    ]


def _parse_timestamp(ts: Optional[int]) -> Optional[str]:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def get_library_items(library_key: str, library_type: str) -> list[dict[str, Any]]:
    with _client() as client:
        resp = client.get(f"/library/sections/{library_key}/all")
        resp.raise_for_status()
        items = resp.json()["MediaContainer"].get("Metadata", [])

    result = []
    for item in items:
        if library_type == "show":
            # Recursively fetch episodes for shows
            result.extend(_get_episodes(item))
        else:
            result.append(_parse_item(item, library_type))
    return result


def _parse_item(item: dict, item_type: str) -> dict[str, Any]:
    file_paths: list[str] = []
    file_size: int = 0
    for media in item.get("Media", []):
        for part in media.get("Part", []):
            if part.get("file"):
                file_paths.append(part["file"])
            file_size += part.get("size", 0)

    return {
        "title": item.get("title", ""),
        "type": item_type,
        "rating_key": item.get("ratingKey", ""),
        "file_paths": file_paths,
        "file_size": file_size,
        "view_count": item.get("viewCount", 0),
        "last_viewed_at": _parse_timestamp(item.get("lastViewedAt")),
        "added_at": _parse_timestamp(item.get("addedAt")),
        "year": item.get("year"),
    }


def _get_episodes(show: dict) -> list[dict[str, Any]]:
    rating_key = show.get("ratingKey")
    episodes = []
    with _client() as client:
        try:
            resp = client.get(f"/library/metadata/{rating_key}/allLeaves")
            resp.raise_for_status()
            items = resp.json()["MediaContainer"].get("Metadata", [])
        except Exception:
            return []

    for ep in items:
        parsed = _parse_item(ep, "episode")
        parsed["show_title"] = show.get("title", "")
        episodes.append(parsed)
    return episodes


def get_all_items() -> list[dict[str, Any]]:
    libraries = get_libraries()
    all_items: list[dict[str, Any]] = []
    for lib in libraries:
        all_items.extend(get_library_items(lib["key"], lib["type"]))
    return all_items
