"""Tests for ignore pattern matching and .treeignore loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from treemark.ignore import DEFAULT_IGNORES, load_treeignore, should_ignore


class TestShouldIgnore:
    def test_exact_name_match(self):
        patterns = ["node_modules", ".git"]
        assert should_ignore("node_modules", "node_modules", patterns=patterns, default_ignores=None)
        assert should_ignore(".git", ".git", patterns=patterns, default_ignores=None)
        assert not should_ignore("src", "src", patterns=patterns, default_ignores=None)

    def test_glob_pattern_match(self):
        patterns = ["*.log", "*.pyc"]
        assert should_ignore("debug.log", "debug.log", patterns=patterns, default_ignores=None)
        assert should_ignore("module.pyc", "module.pyc", patterns=patterns, default_ignores=None)
        assert not should_ignore("main.py", "main.py", patterns=patterns, default_ignores=None)

    def test_path_pattern_match(self):
        patterns = ["src/secret.txt", "data/*.csv"]
        assert should_ignore("secret.txt", "src/secret.txt", patterns=patterns, default_ignores=None)
        assert should_ignore("data.csv", "data/data.csv", patterns=patterns, default_ignores=None)

    def test_default_ignores(self):
        assert should_ignore(".git", ".git", patterns=[], default_ignores=DEFAULT_IGNORES)
        assert should_ignore("node_modules", "node_modules", patterns=[], default_ignores=DEFAULT_IGNORES)
        assert not should_ignore("src", "src", patterns=[], default_ignores=DEFAULT_IGNORES)

    def test_no_default_ignores(self):
        assert not should_ignore(".git", ".git", patterns=[], default_ignores=set())
        assert not should_ignore("node_modules", "node_modules", patterns=[], default_ignores=set())

    def test_empty_patterns(self):
        assert not should_ignore("anything", "anything", patterns=[], default_ignores=None)


class TestLoadTreeignore:
    def test_load_treeignore_file(self, tmp_path):
        gi = tmp_path / ".treeignore"
        gi.write_text("node_modules\n*.log\n# comment\n\nsrc/secret\n")

        patterns = load_treeignore(tmp_path)
        assert "node_modules" in patterns
        assert "*.log" in patterns
        assert "src/secret" in patterns
        assert len(patterns) == 3  # comment and blank line excluded

    def test_no_treeignore_returns_empty(self, tmp_path):
        patterns = load_treeignore(tmp_path)
        assert patterns == []

    def test_explicit_ignore_file(self, tmp_path):
        gi = tmp_path / "custom.ignore"
        gi.write_text("dist\nbuild\n")

        patterns = load_treeignore(tmp_path, explicit_path=str(gi))
        assert "dist" in patterns
        assert "build" in patterns

    def test_explicit_ignore_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_treeignore(tmp_path, explicit_path=str(tmp_path / "nonexistent"))
