import json
import time
from pathlib import Path
from typing import Any, Optional

_CACHE_DIR = Path(__file__).parent.parent / ".cache"


def _path(key: str) -> Path:
    _CACHE_DIR.mkdir(exist_ok=True)
    return _CACHE_DIR / f"{key}.json"


def get(key: str, max_age_hours: int = 24) -> Optional[Any]:
    if max_age_hours == 0:
        return None
    p = _path(key)
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        if (time.time() - payload["ts"]) / 3600 > max_age_hours:
            return None
        return payload["data"]
    except Exception:
        return None


def set(key: str, data: Any) -> None:
    _path(key).write_text(
        json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False),
        encoding="utf-8",
    )


def clear(key: str) -> None:
    p = _path(key)
    if p.exists():
        p.unlink()


def clear_all() -> None:
    if _CACHE_DIR.exists():
        for f in _CACHE_DIR.glob("*.json"):
            f.unlink()


def info(key: str) -> Optional[dict]:
    p = _path(key)
    if not p.exists():
        return None
    try:
        ts = json.loads(p.read_text(encoding="utf-8"))["ts"]
        return {"age_seconds": int(time.time() - ts)}
    except Exception:
        return None
