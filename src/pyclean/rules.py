from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pyclean.models import CleanupMode
from pyclean.utils import matches_any_pattern

DANGEROUS_PATHS = {
    Path("/"),
    Path.home(),
}

WINDOWS_DANGEROUS_SUFFIXES = {
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "users",
}


def resolve_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_dangerous_path(path: Path) -> bool:
    resolved = resolve_path(path)
    if resolved in DANGEROUS_PATHS:
        return True
    if resolved.parent == resolved:
        return True
    if os.name == "nt" and resolved.name.lower() in WINDOWS_DANGEROUS_SUFFIXES:
        return True
    return False


def default_temp_roots() -> tuple[Path, ...]:
    candidates = {
        resolve_path(Path(tempfile.gettempdir())),
    }
    for env_name in ("TMPDIR", "TEMP", "TMP"):
        env_value = os.getenv(env_name)
        if env_value:
            candidates.add(resolve_path(Path(env_value)))
    return tuple(sorted(candidates))


def default_cache_roots() -> tuple[Path, ...]:
    candidates: set[Path] = set()

    xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache:
        candidates.add(resolve_path(Path(xdg_cache)))
    else:
        candidates.add(resolve_path(Path.home() / ".cache"))

    if os.name == "nt":
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            root = resolve_path(Path(local_appdata))
            for relative in (
                Path("pip") / "Cache",
                Path("npm-cache"),
                Path("Temp") / "pip-build",
            ):
                candidates.add(root / relative)

    return tuple(sorted(path for path in candidates if path.exists() or path.parent.exists()))


def allowed_roots_for_mode(mode: CleanupMode) -> tuple[Path, ...]:
    return default_temp_roots() if mode == "temp" else default_cache_roots()


def is_within_allowed_roots(path: Path, allowed_roots: tuple[Path, ...]) -> bool:
    resolved = resolve_path(path)
    for root in allowed_roots:
        resolved_root = resolve_path(root)
        if resolved == resolved_root or resolved_root in resolved.parents:
            return True
    return False


def validate_cleanup_root(path: Path, mode: CleanupMode) -> Path:
    resolved = resolve_path(path)
    if is_dangerous_path(resolved):
        raise ValueError(f"refusing dangerous cleanup path: {resolved}")
    allowed_roots = allowed_roots_for_mode(mode)
    if not is_within_allowed_roots(resolved, allowed_roots):
        raise ValueError(
            f"path {resolved} is outside the safe {mode} cleanup allowlist"
        )
    return resolved


def should_exclude(path: Path, exclude: tuple[str, ...]) -> bool:
    return matches_any_pattern(path, exclude)
