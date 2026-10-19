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
    _scan_dir(root, root_entry, root, opts, patterns, default_ignores, exclude_path, 0)

    if opts.files_only:
        _prune_dirs_without_files(root_entry)

    return root_entry


def _rel_posix(entry: Path, root: Path) -> str:
    """Return the entry's POSIX-style path relative to the scan root.

    Using the scan root (rather than the parent of the directory being walked)
    keeps ignore patterns depth-independent: ``a/b/c.txt`` always refers to the
    same entry no matter how deeply nested it is.
    """
    try:
        return entry.relative_to(root).as_posix()
    except ValueError:
        return entry.name


def _prune_dirs_without_files(entry: Entry) -> None:
    """Drop directories that contain no files anywhere below them.

    Used by ``--files-only`` so that a directory holding only other (possibly
    empty) directories is not shown. Runs bottom-up over the already-built
    tree, so it costs a single pass rather than re-walking each subtree.
    """
    for child in entry.children:
        if child.is_dir:
            _prune_dirs_without_files(child)
    entry.children = [child for child in entry.children if not child.is_dir or child.children]


def _scan_dir(
    dirpath: Path,
    parent: Entry,
    root: Path,
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
    except OSError as exc:
        detail = f" ({exc.strerror})" if getattr(exc, "strerror", None) else ""
        print(f"Warning: cannot read directory: {dirpath}{detail}", file=sys.stderr)
        return

    real_dirs: list[Path] = []
    symlink_dirs: list[Path] = []
    files: list[Path] = []

    for entry in entries:
        name = entry.name

        # Exclude the output file if it's exactly this entry
        if exclude_path is not None and entry.resolve() == exclude_path:
            continue

        # Hidden file filtering (dot-prefixed names)
        if not opts.show_all and name.startswith("."):
            continue

        if should_ignore(
            name,
            _rel_posix(entry, root),
            patterns=patterns,
            default_ignores=default_ignores,
            is_dir=entry.is_dir(),
        ):
            continue

        # Classify. Symlinks are never followed, so they can only be leaves.
        if entry.is_symlink():
            if entry.is_dir():
                symlink_dirs.append(entry)
            else:
                # Symlink to a file (or a broken link) behaves like a file.
                files.append(entry)
        elif entry.is_dir():
            real_dirs.append(entry)
        else:
            files.append(entry)

    # Sort: directories first, then files; alphabetical case-insensitive
    real_dirs.sort(key=lambda p: p.name.lower())
    symlink_dirs.sort(key=lambda p: p.name.lower())
    files.sort(key=lambda p: p.name.lower())

    for d in real_dirs:
        child = Entry(name=d.name, is_dir=True, is_symlink=False)
        parent.children.append(child)
        _scan_dir(d, child, root, opts, patterns, default_ignores, exclude_path, current_depth + 1)

    # Symlinked directories are shown but never descended into.
    for d in symlink_dirs:
        if not opts.files_only:
            parent.children.append(Entry(name=d.name, is_dir=True, is_symlink=True))

    if not opts.dirs_only:
        for f in files:
            parent.children.append(Entry(name=f.name, is_dir=False, is_symlink=f.is_symlink()))
