from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import truenas
import plex
import analyzer

app = FastAPI(title="TrueNAS + Plex Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Simple in-memory cache so repeated frontend refreshes don't hammer the APIs
# ---------------------------------------------------------------------------
_cache: dict[str, Any] = {}


def _get_nas_files() -> list[dict]:
    if "nas_files" not in _cache:
        _cache["nas_files"] = truenas.get_all_files()
    return _cache["nas_files"]


def _get_plex_items() -> list[dict]:
    if "plex_items" not in _cache:
        _cache["plex_items"] = plex.get_all_items()
    return _cache["plex_items"]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/files")
def get_files() -> list[dict]:
    try:
        return _get_nas_files()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/libraries")
def get_plex_libraries() -> list[dict]:
    try:
        return plex.get_libraries()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/items")
def get_plex_items() -> list[dict]:
    try:
        return _get_plex_items()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/unwatched")
def get_unwatched() -> list[dict]:
    try:
        return analyzer.never_watched(_get_plex_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/stale")
def get_stale() -> list[dict]:
    try:
        return analyzer.stale_items(_get_plex_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/nas/orphaned")
def get_orphaned() -> list[dict]:
    try:
        return analyzer.orphaned_files(_get_nas_files(), _get_plex_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/summary")
def get_summary() -> dict:
    try:
        nas_files = _get_nas_files()
        plex_items = _get_plex_items()
        orphans = analyzer.orphaned_files(nas_files, plex_items)
        never = analyzer.never_watched(plex_items)
        stale = analyzer.stale_items(plex_items)
        return analyzer.summary(nas_files, plex_items, orphans, never, stale)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.delete("/cache")
def clear_cache() -> dict:
    _cache.clear()
    return {"status": "cache cleared"}
