"""Tests for output formatting."""

from __future__ import annotations

import pytest

from treemark.output import EMOJI_MAP, _get_emoji, format_markdown, render_tree, safe_print
from treemark.tree import Entry


def _make_simple_tree():
    """Create a simple test tree."""
    root = Entry(name="project", is_dir=True, is_symlink=False)
    src = Entry(name="src", is_dir=True, is_symlink=False)
    src.children.append(Entry(name="main.py", is_dir=False, is_symlink=False))
    root.children.append(src)
    root.children.append(Entry(name="README.md", is_dir=False, is_symlink=False))
    return root


class TestRenderTree:
    def test_simple_tree(self):
        root = _make_simple_tree()
        output = render_tree(root)
        # render_tree only renders children, not the root itself
        assert "src/" in output
        assert "main.py" in output
        assert "README.md" in output

    def test_unicode_characters(self):
        root = _make_simple_tree()
        output = render_tree(root, use_ascii=False)
        # Should use box-drawing characters
        assert "\u251c\u2500\u2500" in output or "\u2514\u2500\u2500" in output

    def test_ascii_characters(self):
        root = _make_simple_tree()
        output = render_tree(root, use_ascii=True)
        assert "+-- " in output or "\\-- " in output

    def test_emoji_mode(self):
        root = _make_simple_tree()
        output = render_tree(root, use_emoji=True)
        assert "\U0001f4c1" in output  # folder emoji
        assert "\U0001f4dd" in output  # memo emoji for .md

    def test_empty_tree(self):
        root = Entry(name="empty", is_dir=True, is_symlink=False)
        output = render_tree(root)
        # Root name should be present but no children rendered
        assert output == ""


class TestFormatMarkdown:
    def test_basic_markdown(self):
        tree_text = "project/\n├── src/\n└── README.md"
        md = format_markdown(tree_text)
        assert md.startswith("```text\n")
        assert md.endswith("\n```")
        assert tree_text in md

    def test_markdown_fence_escaping(self):
        tree_text = "project/\n├── ```\n└── test"
        md = format_markdown(tree_text)
        # The fence must be longer than the longest backtick run it contains.
        assert md.startswith("````text\n")
        assert md.endswith("\n````")
        assert tree_text in md

    @pytest.mark.parametrize("run", range(0, 12))
    def test_fence_is_always_longer_than_content(self, run):
        """A file name of N backticks must never break out of the code block."""
        tree_text = "project/\n" + "`" * run
        md = format_markdown(tree_text)
        fence = md.split("\n", 1)[0]
        expected = "`" * max(3, run + 1) + "text"
        assert fence == expected
        assert tree_text in md

    def test_fence_never_shorter_than_three(self):
        md = format_markdown("project/\n└── a.md")
        assert md.startswith("```text\n")

    def test_no_triple_backticks(self):
        tree_text = "project/\n├── src/\n└── test"
        md = format_markdown(tree_text)
        assert md.startswith("```text\n")


class TestGetEmoji:
    def test_known_extensions(self):
        assert _get_emoji("main.py") == EMOJI_MAP[".py"]
        assert _get_emoji("README.md") == EMOJI_MAP[".md"]
        assert _get_emoji("app.ts") == EMOJI_MAP[".ts"]

    def test_extension_matching_is_case_insensitive(self):
        assert _get_emoji("MAIN.PY") == EMOJI_MAP[".py"]
        assert _get_emoji("readme.MD") == EMOJI_MAP[".md"]

    def test_special_filenames_case_insensitive(self):
        assert _get_emoji("Dockerfile") == EMOJI_MAP["Dockerfile"]
        assert _get_emoji("dockerfile") == EMOJI_MAP["Dockerfile"]
        assert _get_emoji("Makefile") == EMOJI_MAP["Makefile"]
        assert _get_emoji("docker-compose.yml") == EMOJI_MAP["Dockerfile"]

    def test_no_emoji_for_unknown(self):
        assert _get_emoji("mystery.zzz") == ""
        assert _get_emoji("LICENSE") == ""

    def test_suffix_does_not_match_partial_name(self):
        # "app.rsx" must not be treated as a Rust file
        assert _get_emoji("app.rsx") == ""


class TestSafePrint:
    def test_writes_text_and_newline(self, capsys):
        safe_print("hello")
        assert capsys.readouterr().out == "hello\n"

    def test_falls_back_when_encoding_rejects_characters(self, capsys):
        """A terminal that can't encode emoji must not crash or dump raw bytes."""

        class Fussy:
            encoding = "ascii"

            def __init__(self):
                self.chunks = []

            def write(self, s):
                s.encode(self.encoding)  # raise for non-ASCII, like a real stream
                self.chunks.append(s)

        target = Fussy()
        safe_print("ok -> 🐍", file=target)
        assert len(target.chunks) == 1
        assert target.chunks[0] == "ok -> ?\n"
        assert "�" not in target.chunks[0]
