"""Tests for output formatting."""

from __future__ import annotations

from treemark.output import format_markdown, render_tree
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
        # Should use longer fence to avoid conflict
        assert md.startswith("`````")
        assert md.endswith("\n`````")

    def test_no_triple_backticks(self):
        tree_text = "project/\n├── src/\n└── test"
        md = format_markdown(tree_text)
        assert md.startswith("```text\n")
