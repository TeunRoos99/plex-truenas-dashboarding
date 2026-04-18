from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Any
import truenas
import plex
import analyzer
import cache as disk_cache
from config import CACHE_TTL_HOURS

app = FastAPI(title="TrueNAS + Plex Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "DELETE"],
    allow_headers=["*"],
)

# In-memory layer (fastest, lives for the duration of the process)
_mem: dict[str, Any] = {}


async def _nas_files() -> list:
    if "nas_files" in _mem:
        return _mem["nas_files"]
    cached = disk_cache.get("nas_files", CACHE_TTL_HOURS)
    if cached is not None:
        _mem["nas_files"] = cached
        return cached
    data = await truenas.get_all_files()
    disk_cache.set("nas_files", data)
    _mem["nas_files"] = data
    return data


async def _plex_items() -> list:
    if "plex_items" in _mem:
        return _mem["plex_items"]
    cached = disk_cache.get("plex_items", CACHE_TTL_HOURS)
    if cached is not None:
        _mem["plex_items"] = cached
        return cached
    data = await asyncio.to_thread(plex.get_all_items)
    disk_cache.set("plex_items", data)
    _mem["plex_items"] = data
    return data


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/files")
async def get_files() -> list:
    try:
        return await _nas_files()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/libraries")
async def get_plex_libraries() -> list:
    try:
        return await asyncio.to_thread(plex.get_libraries)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/items")
async def get_plex_items() -> list:
    try:
        return await _plex_items()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/unwatched")
async def get_unwatched() -> list:
    try:
        return analyzer.never_watched(await _plex_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/plex/stale")
async def get_stale() -> list:
    try:
        return analyzer.stale_items(await _plex_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/nas/orphaned")
async def get_orphaned() -> list:
    try:
        return analyzer.orphaned_files(await _nas_files(), await _plex_items())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/summary")
async def get_summary() -> dict:
    try:
        nas_files = await _nas_files()
        plex_items = await _plex_items()
        orphans = analyzer.orphaned_files(nas_files, plex_items)
        never = analyzer.never_watched(plex_items)
        stale = analyzer.stale_items(plex_items)
        result = analyzer.summary(nas_files, plex_items, orphans, never, stale)

        nas_info = disk_cache.info("nas_files")
        plex_info = disk_cache.info("plex_items")
        result["nas_cache_age_hours"] = round(nas_info["age_seconds"] / 3600, 1) if nas_info else None
        result["plex_cache_age_hours"] = round(plex_info["age_seconds"] / 3600, 1) if plex_info else None
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.delete("/cache")
async def clear_cache() -> dict:
    _mem.clear()
    disk_cache.clear_all()
    return {"status": "cache cleared"}
