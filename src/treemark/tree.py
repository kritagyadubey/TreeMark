"""Scan directories and build the tree structure."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from treemark.ignore import DEFAULT_IGNORES, load_treeignore, should_ignore


@dataclass
class TreeOptions:
    """All options that control how the tree is built and displayed."""

    show_all: bool = False
    depth: int | None = None  # None = unlimited
    files_only: bool = False
    dirs_only: bool = False
    ignore_patterns: list[str] = field(default_factory=list)
    ignore_file: str | None = None
    no_default_ignore: bool = False
    use_emoji: bool = False
    use_ascii: bool = False
    output_file: str | None = None
    markdown: bool = False


@dataclass
class Entry:
    """A single entry in the tree (file or directory)."""

    name: str
    is_dir: bool
    is_symlink: bool
    children: list["Entry"] = field(default_factory=list)


def build_tree(root: Path, opts: TreeOptions) -> Entry:
    """Scan root and return the tree as an Entry with children."""
    root = root.resolve()
    if not root.exists():
        raise SystemExit(f"Error: directory does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Error: path is not a directory: {root}")

    default_ignores: set[str] | None = None if opts.no_default_ignore else DEFAULT_IGNORES.copy()

    patterns: list[str] = []
    for p in opts.ignore_patterns:
        patterns.extend(item.strip() for item in p.split(",") if item.strip())
    try:
        patterns.extend(load_treeignore(root, opts.ignore_file))
    except FileNotFoundError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    # Resolve the output file to exclude it later
    exclude_path: Path | None = None
    if opts.output_file:
        out = Path(opts.output_file).resolve()
        try:
            out.relative_to(root)
            exclude_path = out
        except ValueError:
            pass  # output file is outside the scan root

    root_entry = Entry(name=root.name, is_dir=True, is_symlink=False)
    _scan_dir(root, root_entry, opts, patterns, default_ignores, exclude_path, 0)
    return root_entry


def _scan_dir(
    dirpath: Path,
    parent: Entry,
    opts: TreeOptions,
    patterns: list[str],
    default_ignores: set[str] | None,
    exclude_path: Path | None,
    current_depth: int,
) -> None:
    """Recursively scan a directory and populate parent.children."""
    if opts.depth is not None and current_depth >= opts.depth:
        return

    try:
        entries = list(dirpath.iterdir())
    except PermissionError:
        print(f"Warning: cannot read directory: {dirpath}", file=sys.stderr)
        return

    dirs: list[Path] = []
    files: list[Path] = []

    for entry in entries:
        name = entry.name

        # Exclude the output file if it's exactly this entry
        if exclude_path is not None and entry.resolve() == exclude_path:
            continue

        # Hidden file filtering (dot-prefixed names)
        if not opts.show_all and name.startswith("."):
            continue

        # Build relative POSIX path for pattern matching
        try:
            rel_posix = str(entry.relative_to(dirpath.parent).as_posix())
        except ValueError:
            rel_posix = name

        if should_ignore(name, rel_posix, patterns=patterns, default_ignores=default_ignores):
            continue

        is_symlink = entry.is_symlink()
        is_dir = entry.is_dir() if not is_symlink else False

        if is_dir and not is_symlink:
            dirs.append(entry)
        elif is_dir and is_symlink:
            # Symlink to directory: treat as leaf, don't descend
            parent.children.append(Entry(name=name, is_dir=True, is_symlink=True))
        else:
            files.append(entry)

    # Sort: directories first, then files; alphabetical case-insensitive
    dirs.sort(key=lambda p: p.name.lower())
    files.sort(key=lambda p: p.name.lower())

    for d in dirs:
        child = Entry(name=d.name, is_dir=True, is_symlink=False)
        if not opts.files_only or _dir_has_visible_files(d, opts, patterns, default_ignores, exclude_path):
            parent.children.append(child)
        _scan_dir(d, child, opts, patterns, default_ignores, exclude_path, current_depth + 1)

    for f in files:
        if not opts.dirs_only:
            parent.children.append(Entry(name=f.name, is_dir=False, is_symlink=f.is_symlink()))


def _dir_has_visible_files(
    dirpath: Path,
    opts: TreeOptions,
    patterns: list[str],
    default_ignores: set[str] | None,
    exclude_path: Path | None,
) -> bool:
    """Check if a directory contains any visible files (used for --files-only)."""
    try:
        for entry in dirpath.iterdir():
            if not opts.show_all and entry.name.startswith("."):
                continue
            if exclude_path is not None and entry.resolve() == exclude_path:
                continue
            rel_posix = str(entry.relative_to(dirpath.parent).as_posix())
            if should_ignore(entry.name, rel_posix, patterns=patterns, default_ignores=default_ignores):
                continue
            if entry.is_file():
                return True
            if entry.is_dir():
                return True
    except PermissionError:
        return False
    return False
