import httpx
from typing import Any
from config import TRUENAS_URL, TRUENAS_API_KEY, TRUENAS_VERIFY_SSL


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=f"{TRUENAS_URL.rstrip('/')}/api/v2.0",
        headers={"Authorization": f"Bearer {TRUENAS_API_KEY}"},
        verify=TRUENAS_VERIFY_SSL,
        timeout=60,
    )


def get_datasets() -> list[dict[str, Any]]:
    with _client() as client:
        resp = client.get("/pool/dataset", params={"extra": {"retrieve_children": True}})
        resp.raise_for_status()
        return resp.json()


def _flatten_datasets(datasets: list[dict], result: list) -> None:
    for ds in datasets:
        result.append(ds)
        children = ds.get("children") or []
        _flatten_datasets(children, result)


def list_files(path: str) -> list[dict[str, Any]]:
    """List files recursively under a given path via TrueNAS filesystem/listdir."""
    files: list[dict[str, Any]] = []
    _recurse_dir(path, files)
    return files


def _recurse_dir(path: str, files: list) -> None:
    with _client() as client:
        try:
            resp = client.post(
                "/filesystem/listdir",
                json={"path": path, "query-filters": [], "query-options": {}},
            )
            resp.raise_for_status()
            entries = resp.json()
        except Exception:
            return

    for entry in entries:
        if entry.get("type") == "DIRECTORY":
            _recurse_dir(entry["path"], files)
        else:
            files.append(
                {
                    "path": entry.get("path", ""),
                    "name": entry.get("name", ""),
                    "size": entry.get("size", 0),
                    "type": entry.get("type", ""),
                    "modified": entry.get("mtime", 0),
                }
            )


def get_all_files() -> list[dict[str, Any]]:
    """Fetch all files from all datasets."""
    datasets: list[dict] = []
    raw = get_datasets()
    _flatten_datasets(raw, datasets)

    seen_paths: set[str] = set()
    all_files: list[dict[str, Any]] = []

    for ds in datasets:
        mount = ds.get("mountpoint")
        if not mount or mount in seen_paths:
            continue
        seen_paths.add(mount)
        all_files.extend(list_files(mount))

    return all_files
