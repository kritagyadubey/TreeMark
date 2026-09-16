"""CLI entry point for TreeMark."""

from __future__ import annotations

import argparse
from pathlib import Path

from treemark import __version__
from treemark.output import format_markdown, render_tree, safe_print
from treemark.tree import TreeOptions, build_tree


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the treemark CLI."""
    args = _parse_args(argv)

    opts = TreeOptions(
        show_all=args.all,
        depth=args.depth,
        files_only=args.files_only,
        dirs_only=args.dirs_only or args.no_files,
        ignore_patterns=args.ignore or [],
        ignore_file=args.ignore_file,
        no_default_ignore=args.no_default_ignore,
        use_emoji=args.emoji,
        use_ascii=args.ascii,
        output_file=args.output,
        markdown=args.markdown,
    )

    root = Path(args.path).resolve()

    try:
        tree = build_tree(root, opts)
    except SystemExit as exc:
        raise exc from None

    tree_text = render_tree(tree, use_emoji=opts.use_emoji, use_ascii=opts.use_ascii)

    # Build full output: root line + children
    root_name = root.name + "/"
    full_tree = root_name + ("\n" + tree_text if tree_text else "")

    if opts.markdown:
        full_tree = format_markdown(full_tree)

    if args.output:
        _write_output(args.output, full_tree)
    else:
        safe_print(full_tree)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="treemark",
        description="Generate clean project trees for Markdown, READMEs, docs, and terminals.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  treemark                        Scan current directory
  treemark path/to/project        Scan a specific directory
  treemark --depth 2              Limit to 2 levels deep
  treemark --all                  Include hidden files
  treemark --files-only           Show only files
  treemark --ignore node_modules  Ignore specific directories
  treemark --markdown             Output as Markdown code block
  treemark --emoji                Show file type emojis
  treemark --ascii                Use ASCII tree characters
  treemark --output tree.md       Write output to file
""",
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Maximum depth to scan (default: unlimited)",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Include hidden files and directories",
    )
    parser.add_argument(
        "--files-only",
        action="store_true",
        help="Show only files (directories shown only if they contain visible files)",
    )
    parser.add_argument(
        "--dirs-only",
        action="store_true",
        help="Show only directories",
    )
    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Alias for --dirs-only",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        help="Comma-separated patterns to ignore (may be repeated)",
    )
    parser.add_argument(
        "--ignore-file",
        default=None,
        help="Path to ignore file (default: auto-load .treeignore if present)",
    )
    parser.add_argument(
        "--no-default-ignore",
        action="store_true",
        help="Disable built-in default ignore patterns",
    )
    parser.add_argument(
        "--markdown", "-m",
        action="store_true",
        help="Output as a Markdown fenced code block",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Output plain tree (default)",
    )
    parser.add_argument(
        "--emoji",
        action="store_true",
        help="Show emojis for common file types",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Use ASCII tree characters instead of Unicode",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to a file instead of stdout",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    if args.depth is not None and args.depth < 0:
        parser.error("depth must be a non-negative integer")

    return args


def _write_output(path: str, content: str) -> None:
    """Write content to the output file, creating parent dirs if needed."""
    out = Path(path)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content + "\n", encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Error: could not write to {path}: {exc}") from exc
