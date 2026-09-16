"""Format the tree for display: plain, markdown, emoji, or ASCII."""

from __future__ import annotations

import sys

from treemark.tree import Entry

# Emoji map for common file types
EMOJI_MAP: dict[str, str] = {
    ".py": "\U0001f40d",    # snake
    ".js": "\U0001f7e8",    # yellow square
    ".ts": "\U0001f4d8",    # blue book
    ".html": "\U0001f310",  # globe
    ".css": "\U0001f3a8",   # artist palette
    ".json": "\U0001f4e6",  # package
    ".md": "\U0001f4dd",    # memo
    ".yml": "\u2699\ufe0f", # gear
    ".yaml": "\u2699\ufe0f",# gear
    ".toml": "\u2699\ufe0f",# gear
    "Dockerfile": "\U0001f433",  # whale
}

# Unicode box-drawing characters
BRANCH = "\u251c\u2500\u2500 "
LAST_BRANCH = "\u2514\u2500\u2500 "
PIPE = "\u2502   "
SPACE = "    "

# ASCII fallback
ASCII_BRANCH = "+-- "
ASCII_LAST_BRANCH = "\\-- "
ASCII_PIPE = "|   "
ASCII_SPACE = "    "


def render_tree(entry: Entry, *, use_emoji: bool = False, use_ascii: bool = False) -> str:
    """Render the tree entry into a list of lines."""
    lines: list[str] = []
    _render_entry(entry, lines, "", use_emoji=use_emoji, use_ascii=use_ascii)
    return "\n".join(lines)


def _render_entry(
    entry: Entry,
    lines: list[str],
    prefix: str,
    *,
    use_emoji: bool,
    use_ascii: bool,
) -> None:
    branch = ASCII_BRANCH if use_ascii else BRANCH
    last = ASCII_LAST_BRANCH if use_ascii else LAST_BRANCH
    pipe = ASCII_PIPE if use_ascii else PIPE
    space = ASCII_SPACE if use_ascii else SPACE

    children = entry.children
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        connector = last if is_last else branch

        display_name = child.name
        if child.is_dir:
            display_name += "/"
        if use_emoji and not child.is_dir:
            emoji = _get_emoji(child.name)
            if emoji:
                display_name = f"{emoji} {display_name}"
        elif use_emoji and child.is_dir:
            display_name = f"\U0001f4c1 {display_name}"

        if child.is_symlink:
            display_name += " -> (symlink)"

        lines.append(f"{prefix}{connector}{display_name}")

        if child.is_dir and child.children:
            extension = space if is_last else pipe
            _render_entry(child, lines, prefix + extension, use_emoji=use_emoji, use_ascii=use_ascii)


def _get_emoji(filename: str) -> str:
    """Get the emoji for a filename based on its extension."""
    lower = filename.lower()
    for ext, emoji in EMOJI_MAP.items():
        if ext.startswith(".") and lower.endswith(ext):
            return emoji
    # Check special filenames
    if filename in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"):
        return EMOJI_MAP.get("Dockerfile", "")
    return ""


def format_markdown(tree_text: str) -> str:
    """Wrap tree output in a markdown fenced code block.

    Automatically uses longer fence if the tree contains triple backticks.
    """
    fence = "```"
    if "```" in tree_text:
        fence = "`````"
    return f"{fence}text\n{tree_text}\n{fence}"


def safe_print(text: str, file=None) -> None:
    """Print text, falling back to ASCII-safe encoding on terminals that can't handle Unicode."""
    target = file or sys.stdout
    try:
        target.write(text + "\n")
    except UnicodeEncodeError:
        # Fallback: encode with replacement characters
        target.buffer.write((text + "\n").encode("utf-8", errors="replace"))
