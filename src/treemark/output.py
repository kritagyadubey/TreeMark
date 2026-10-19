"""Format the tree for display: plain, markdown, emoji, or ASCII."""

from __future__ import annotations

import sys

from treemark.tree import Entry

# Emoji map for common file types. Keys are matched by suffix (dot-prefixed)
# or, for extension-less names, exactly.
EMOJI_MAP: dict[str, str] = {
    ".py": "\U0001f40d",    # snake
    ".js": "\U0001f7e8",    # yellow square
    ".jsx": "\U0001f7e8",
    ".ts": "\U0001f4d8",    # blue book
    ".tsx": "\U0001f4d8",
    ".vue": "\U0001f7e9",
    ".svelte": "\U0001f7e9",
    ".html": "\U0001f310",  # globe
    ".css": "\U0001f3a8",   # artist palette
    ".scss": "\U0001f3a8",
    ".json": "\U0001f4e6",  # package
    ".md": "\U0001f4dd",    # memo
    ".rst": "\U0001f4dd",
    ".txt": "\U0001f4c4",   # page facing up
    ".yml": "\u2699\ufe0f", # gear
    ".yaml": "\u2699\ufe0f",
    ".toml": "\u2699\ufe0f",
    ".ini": "\u2699\ufe0f",
    ".cfg": "\u2699\ufe0f",
    ".conf": "\u2699\ufe0f",
    ".xml": "\u2699\ufe0f",
    ".lock": "\U0001f512",  # lock
    ".sh": "\U0001f4df",    # telephone receiver
    ".bash": "\U0001f4df",
    ".zsh": "\U0001f4df",
    ".ps1": "\U0001f4df",
    ".bat": "\U0001f4df",
    ".cmd": "\U0001f4df",
    ".go": "\U0001f42d",    # mouse face
    ".rs": "\U0001f980",    # crab
    ".java": "\U0001f34a",  # orange
    ".kt": "\U0001f34a",
    ".c": "\U0001f5a5\ufe0f",   # desktop computer
    ".h": "\U0001f5a5\ufe0f",
    ".cpp": "\U0001f5a5\ufe0f",
    ".hpp": "\U0001f5a5\ufe0f",
    ".cs": "\U0001f5a5\ufe0f",
    ".rb": "\U0001f7e3",    # green square
    ".php": "\U0001f49b",   # yellow heart
    ".swift": "\U0001f34a",
    ".sql": "\U0001f5c3\ufe0f",  # card file box
    ".ipynb": "\U0001f9e0", # brain
    ".r": "\U0001f7e2",
    ".lua": "\U0001f422",
    ".png": "\U0001f5bc\ufe0f",  # framed picture
    ".jpg": "\U0001f5bc\ufe0f",
    ".jpeg": "\U0001f5bc\ufe0f",
    ".gif": "\U0001f5bc\ufe0f",
    ".svg": "\U0001f5bc\ufe0f",
    ".ico": "\U0001f5bc\ufe0f",
    ".pdf": "\U0001f4d5",   # closed book
    ".zip": "\U0001f9f0",   # toolbox
    ".gz": "\U0001f9f0",
    ".tar": "\U0001f9f0",
    ".log": "\U0001f4dc",   # scroll
    "Makefile": "\U0001f6e0\ufe0f",  # hammer and wrench
    "Dockerfile": "\U0001f433",      # whale
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
    """Get the emoji for a filename based on its special name or extension.

    Extension-less special names are checked first: ``docker-compose.yml``
    would otherwise be swallowed by the ``.yml`` rule and never reach the
    Docker-specific mapping.
    """
    lower = filename.lower()
    if lower in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
        return EMOJI_MAP["Dockerfile"]
    if lower in ("makefile", "gnumakefile"):
        return EMOJI_MAP["Makefile"]

    for ext, emoji in EMOJI_MAP.items():
        if ext.startswith(".") and lower.endswith(ext):
            return emoji
    return ""


def format_markdown(tree_text: str) -> str:
    """Wrap tree output in a markdown fenced code block.

    The fence is one backtick longer than the longest backtick run inside the
    tree, so a file whose name contains backticks can never break out of the
    block. It is never shorter than three backticks.
    """
    fence = "`" * max(3, _longest_backtick_run(tree_text) + 1)
    return f"{fence}text\n{tree_text}\n{fence}"


def _longest_backtick_run(text: str) -> int:
    """Return the length of the longest consecutive run of backticks."""
    longest = current = 0
    for char in text:
        if char == "`":
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    return longest


def safe_print(text: str, file=None) -> None:
    """Print text, falling back to readable output on terminals that can't handle Unicode.

    If the terminal's encoding rejects a character (common with emoji on the
    Windows console, which defaults to a legacy code page), the line is
    re-encoded with replacement characters instead of crashing or dumping raw
    UTF-8 bytes to the screen.
    """
    target = file or sys.stdout
    try:
        target.write(text + "\n")
    except UnicodeEncodeError:
        encoding = getattr(target, "encoding", None) or "utf-8"
        fallback = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        target.write(fallback + "\n")
