"""Ignore pattern matching and .treeignore file loading."""

from __future__ import annotations

import fnmatch
from pathlib import Path

# Built-in names to ignore by default.
DEFAULT_IGNORES: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".eggs",
    "*.egg-info",
    ".idea",
    ".vscode",
}


def load_treeignore(root: Path, explicit_path: str | None = None) -> list[str]:
    """Load ignore patterns from a .treeignore file.

    If explicit_path is given, use that file. Otherwise, look for .treeignore
    in root and load it if present. Returns an empty list if no file found.
    """
    if explicit_path is not None:
        p = Path(explicit_path)
        if not p.is_file():
            raise FileNotFoundError(f"could not read ignore file: {explicit_path}")
        return _parse_ignore_file(p)

    auto = root / ".treeignore"
    if auto.is_file():
        return _parse_ignore_file(auto)

    return []


def _parse_ignore_file(path: Path) -> list[str]:
    """Parse a .treeignore file into a list of pattern strings."""
    patterns: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def should_ignore(
    name: str,
    rel_path: str,
    *,
    patterns: list[str],
    default_ignores: set[str] | None,
    is_dir: bool = False,
) -> bool:
    """Check whether an entry should be ignored.

    Checks against both the bare name and the POSIX-style path relative to the
    scan root.

    Matching uses :func:`fnmatch.fnmatchcase` so that a given pattern behaves
    identically on Windows, macOS and Linux (``fnmatch.fnmatch`` silently folds
    case on Windows, which made ``.treeignore`` files platform-dependent).

    A pattern ending in ``/`` only matches directories, e.g. ``dist/``.
    """
    if default_ignores is not None:
        for pat in default_ignores:
            if _matches_pattern(name, rel_path, pat, is_dir=is_dir):
                return True

    for pat in patterns:
        if _matches_pattern(name, rel_path, pat, is_dir=is_dir):
            return True

    return False


def _matches_pattern(name: str, rel_path: str, pattern: str, *, is_dir: bool) -> bool:
    """Match a single ignore pattern against an entry name and relative path."""
    if pattern.endswith("/"):
        # Trailing slash = directory-only pattern (gitignore convention).
        if not is_dir:
            return False
        pattern = pattern.rstrip("/")
        if not pattern:
            return False

    return fnmatch.fnmatchcase(name, pattern) or fnmatch.fnmatchcase(rel_path, pattern)
