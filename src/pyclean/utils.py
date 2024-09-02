from __future__ import annotations

import fnmatch
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SIZE_UNITS: dict[str, int] = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
}


def configure_logging(verbose: bool = False) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return logging.getLogger("pyclean")


def parse_size(size: str | int) -> int:
    if isinstance(size, int):
        if size < 0:
            raise ValueError("size must be non-negative")
        return size

    normalized = size.strip().lower()
    if not normalized:
        raise ValueError("size cannot be empty")

    for unit in sorted(SIZE_UNITS, key=len, reverse=True):
        if normalized.endswith(unit):
            value = normalized.removesuffix(unit).strip()
            if not value:
                raise ValueError(f"missing numeric value in size: {size}")
            return int(float(value) * SIZE_UNITS[unit])

    return int(float(normalized))


def format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size_bytes} B"


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def matches_any_pattern(path: Path, patterns: Iterable[str]) -> bool:
    path_text = path.as_posix()
    name = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(path_text, pattern) or fnmatch.fnmatch(name, pattern):
            return True
    return False


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
