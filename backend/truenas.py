import httpx
import asyncio
from typing import Any
from config import TRUENAS_URL, TRUENAS_API_KEY, TRUENAS_VERIFY_SSL, SCAN_PATHS, NAS_CONCURRENCY


def _client_kwargs() -> dict:
    return dict(
        base_url=f"{TRUENAS_URL.rstrip('/')}/api/v2.0",
        headers={"Authorization": f"Bearer {TRUENAS_API_KEY}"},
        verify=TRUENAS_VERIFY_SSL,
        timeout=60,
    )


async def get_datasets() -> list:
    async with httpx.AsyncClient(**_client_kwargs()) as client:
        resp = await client.get("/pool/dataset", params={"extra": {"retrieve_children": True}})
        resp.raise_for_status()
        return resp.json()


def _flatten_datasets(datasets: list, result: list) -> None:
    for ds in datasets:
        result.append(ds)
        _flatten_datasets(ds.get("children") or [], result)


async def _fetch_dir(client: httpx.AsyncClient, path: str, sem: asyncio.Semaphore) -> list:
    async with sem:
        try:
            resp = await client.post(
                "/filesystem/listdir",
                json={"path": path, "query-filters": [], "query-options": {}},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []


async def _recurse_dirs(start_paths: list) -> list:
    sem = asyncio.Semaphore(NAS_CONCURRENCY)
    files: list = []
    queue: list = list(start_paths)

    async with httpx.AsyncClient(**_client_kwargs()) as client:
        while queue:
            batch, queue = queue[:NAS_CONCURRENCY], queue[NAS_CONCURRENCY:]
            results = await asyncio.gather(*[_fetch_dir(client, p, sem) for p in batch])
            for entries in results:
                for entry in entries:
                    if entry.get("type") == "DIRECTORY":
                        queue.append(entry["path"])
                    else:
                        files.append({
                            "path": entry.get("path", ""),
                            "name": entry.get("name", ""),
                            "size": entry.get("size", 0),
                            "modified": entry.get("mtime", 0),
                        })
    return files


async def get_all_files() -> list:
    if SCAN_PATHS:
        return await _recurse_dirs(SCAN_PATHS)

    datasets: list = []
    _flatten_datasets(await get_datasets(), datasets)
    seen: set = set()
    roots: list = []
    for ds in datasets:
        mount = ds.get("mountpoint")
        if mount and mount not in seen:
            seen.add(mount)
            roots.append(mount)
    return await _recurse_dirs(roots)
