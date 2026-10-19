"""Tests for tree building and traversal."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from treemark.cli import main
from treemark.tree import TreeOptions, build_tree


def _collect_names(entry) -> list[str]:
    """Collect all entry names in a flat list for easy assertions."""
    names = [entry.name]
    for child in entry.children:
        names.extend(_collect_names(child))
    return names


def _collect_dirs(entry) -> list[str]:
    """Collect directory names (without trailing /)."""
    names = []
    if entry.is_dir:
        names.append(entry.name)
    for child in entry.children:
        names.extend(_collect_dirs(child))
    return names


def _collect_files(entry) -> list[str]:
    """Collect file names."""
    names = []
    if not entry.is_dir and not entry.is_symlink:
        names.append(entry.name)
    for child in entry.children:
        names.extend(_collect_files(child))
    return names


class TestBasicTreeGeneration:
    def test_simple_flat_directory(self, tmp_path):
        (tmp_path / "file1.txt").write_text("")
        (tmp_path / "file2.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = _collect_names(tree)
        assert "file1.txt" in names
        assert "file2.py" in names

    def test_nested_directories(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        assert len(tree.children) == 2  # src/, tests/
        src = tree.children[0]
        assert src.name == "src"
        assert len(src.children) == 1
        assert src.children[0].name == "main.py"


class TestSorting:
    def test_directories_before_files(self, tmp_path):
        (tmp_path / "abc.txt").write_text("")
        (tmp_path / "zdir").mkdir()
        (tmp_path / "adir").mkdir()

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        # Directories first, then files
        dir_indices = [i for i, n in enumerate(names) if not n.endswith(".txt")]
        file_indices = [i for i, n in enumerate(names) if n.endswith(".txt")]
        if dir_indices and file_indices:
            assert max(dir_indices) < min(file_indices)

    def test_alphabetical_within_category(self, tmp_path):
        (tmp_path / "z_file.txt").write_text("")
        (tmp_path / "a_file.txt").write_text("")
        (tmp_path / "m_file.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert names == sorted(names)

    def test_case_insensitive_sorting(self, tmp_path):
        (tmp_path / "Banana.txt").write_text("")
        (tmp_path / "apple.txt").write_text("")
        (tmp_path / "Cherry.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert names == ["apple.txt", "Banana.txt", "Cherry.txt"]

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows filesystem is case-insensitive",
    )
    def test_tie_breaking_uses_original_name(self, tmp_path):
        (tmp_path / "ABC.txt").write_text("")
        (tmp_path / "abc.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert len(names) == 2


class TestHiddenFiles:
    def test_hidden_files_excluded_by_default(self, tmp_path):
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".env").write_text("")
        (tmp_path / "visible.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert ".hidden" not in names
        assert ".env" not in names
        assert "visible.txt" in names

    def test_hidden_files_with_all_flag(self, tmp_path):
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".env").write_text("")
        (tmp_path / "visible.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(show_all=True))
        names = [c.name for c in tree.children]
        assert ".hidden" in names
        assert ".env" in names
        assert "visible.txt" in names


class TestDepth:
    def test_depth_0(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(depth=0))
        assert len(tree.children) == 0

    def test_depth_1(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(depth=1))
        names = [c.name for c in tree.children]
        assert "src" in names
        assert "tests" in names
        src = next(c for c in tree.children if c.name == "src")
        assert len(src.children) == 0

    def test_depth_2(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "api").mkdir()
        (tmp_path / "src" / "api" / "routes.py").write_text("")
        (tmp_path / "src" / "main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(depth=2))
        src = next(c for c in tree.children if c.name == "src")
        assert len(src.children) == 2  # api/, main.py
        api = next(c for c in src.children if c.name == "api")
        assert len(api.children) == 0  # depth limit

    def test_unlimited_depth(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "c").mkdir()
        (tmp_path / "a" / "b" / "c" / "deep.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(depth=None))
        a = tree.children[0]
        b = a.children[0]
        c = b.children[0]
        assert c.children[0].name == "deep.txt"

    def test_negative_depth_rejected(self):
        with pytest.raises(SystemExit):
            main(["--depth", "-1"])


class TestIgnore:
    def test_ignore_exact_names(self, tmp_path):
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "pkg.js").write_text("")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["node_modules"]))
        names = [c.name for c in tree.children]
        assert "node_modules" not in names
        assert "src" in names

    def test_ignore_glob_patterns(self, tmp_path):
        (tmp_path / "test.log").write_text("")
        (tmp_path / "debug.log").write_text("")
        (tmp_path / "src.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["*.log"]))
        names = [c.name for c in tree.children]
        assert "test.log" not in names
        assert "debug.log" not in names
        assert "src.py" in names

    def test_ignore_path_patterns(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "secret.txt").write_text("")
        (tmp_path / "public.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["src/secret.txt"]))
        src = tree.children[0]
        names = [c.name for c in src.children]
        assert "secret.txt" not in names
        assert "public.txt" in [
            c.name for c in tree.children if not c.is_dir
        ]


class TestDefaultIgnores:
    def test_default_ignores_applied(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert ".git" not in names
        assert "node_modules" not in names
        assert "__pycache__" not in names
        assert "src" in names

    def test_no_default_ignore(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")

        # .git is hidden, so we need show_all=True to see it even with default ignores disabled
        tree = build_tree(tmp_path, TreeOptions(no_default_ignore=True, show_all=True))
        names = [c.name for c in tree.children]
        assert ".git" in names


class TestFilesOnly:
    def test_files_only(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "empty_dir").mkdir()
        (tmp_path / "readme.md").write_text("")

        tree = build_tree(tmp_path, TreeOptions(files_only=True))
        all_names = _collect_names(tree)
        # empty_dir should not appear
        assert "empty_dir" not in all_names
        # src should appear because it has main.py
        assert "src" in all_names
        assert "main.py" in all_names
        assert "readme.md" in all_names


class TestDirsOnly:
    def test_dirs_only(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "tests").mkdir()
        (tmp_path / "README.md").write_text("")

        tree = build_tree(tmp_path, TreeOptions(dirs_only=True))
        all_names = _collect_names(tree)
        assert "main.py" not in all_names
        assert "README.md" not in all_names
        assert "src" in all_names
        assert "tests" in all_names


class TestNoFilesAlias:
    def test_no_files_is_dirs_only(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(dirs_only=True))
        all_names = _collect_names(tree)
        assert "main.py" not in all_names
        assert "src" in all_names


class TestEdgeCases:
    def test_empty_directory(self, tmp_path):
        tree = build_tree(tmp_path, TreeOptions())
        assert len(tree.children) == 0

    def test_invalid_path(self):
        with pytest.raises(SystemExit):
            build_tree(Path("/nonexistent/path"), TreeOptions())

    def test_path_is_file(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("")
        with pytest.raises(SystemExit):
            build_tree(f, TreeOptions())

    def test_filenames_with_spaces(self, tmp_path):
        (tmp_path / "my file.txt").write_text("")
        (tmp_path / "dir with spaces").mkdir()
        (tmp_path / "dir with spaces" / "file.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert "my file.txt" in names
        assert "dir with spaces" in names

    def test_unicode_filenames(self, tmp_path):
        (tmp_path / "données.txt").write_text("")
        (tmp_path / "日本語").mkdir()
        (tmp_path / "日本語" / "ファイル.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert "données.txt" in names
        assert "日本語" in names

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Symlinks require admin privileges on Windows",
    )
    def test_symlinks_not_followed(self, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        (target / "file.txt").write_text("")
        link = tmp_path / "link"
        link.symlink_to(target)

        tree = build_tree(tmp_path, TreeOptions())
        link_entry = next(c for c in tree.children if c.name == "link")
        assert link_entry.is_symlink
        assert len(link_entry.children) == 0

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Symlinks require admin privileges on Windows",
    )
    def test_broken_symlink(self, tmp_path):
        link = tmp_path / "broken_link"
        link.symlink_to(tmp_path / "nonexistent")

        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert "broken_link" in names

    def test_permission_error_skipped(self, tmp_path, monkeypatch):
        (tmp_path / "noaccess").mkdir()

        original_iterdir = Path.iterdir

        def mock_iterdir(self):
            if self.name == "noaccess":
                raise PermissionError()
            return original_iterdir(self)

        monkeypatch.setattr(Path, "iterdir", mock_iterdir)

        # Should not crash
        tree = build_tree(tmp_path, TreeOptions())
        names = [c.name for c in tree.children]
        assert "noaccess" in names  # entry still visible, just no children


class TestOutputExclusion:
    def test_output_file_excluded_when_inside_root(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "tree.md").write_text("")  # this should be excluded

        tree = build_tree(tmp_path, TreeOptions(output_file=str(tmp_path / "tree.md")))
        names = [c.name for c in tree.children]
        assert "tree.md" not in names
        assert "src" in names

    def test_output_file_outside_root_not_excluded(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        other = tmp_path / "other_dir"
        other.mkdir()
        (other / "tree.md").write_text("")

        tree = build_tree(tmp_path, TreeOptions(output_file=str(other / "tree.md")))
        names = _collect_names(tree)
        assert "main.py" in names


class TestIgnorePathsAreRootRelative:
    """Ignore path patterns must resolve against the scan root, not the parent
    of the directory currently being walked (which made them depth-dependent)."""

    def test_deep_path_pattern(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "c.txt").write_text("")
        (tmp_path / "a" / "b" / "keep.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["a/b/c.txt"]))
        a = next(c for c in tree.children if c.name == "a")
        b = next(c for c in a.children if c.name == "b")
        names = [c.name for c in b.children]
        assert "c.txt" not in names
        assert "keep.txt" in names

    def test_root_level_path_pattern(self, tmp_path):
        (tmp_path / "top.txt").write_text("")
        (tmp_path / "other.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["top.txt"]))
        names = [c.name for c in tree.children]
        assert "top.txt" not in names
        assert "other.txt" in names

    def test_pattern_is_depth_independent(self, tmp_path):
        """The same pattern must match the same shape at any depth."""
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "target.txt").write_text("")
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "target.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["*/target.txt"]))
        assert [n for n in _collect_names(tree) if n == "target.txt"] == []

    def test_directory_only_pattern_ignores_only_directories(self, tmp_path):
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "out.js").write_text("")
        (tmp_path / "dist.py").write_text("")

        tree = build_tree(tmp_path, TreeOptions(ignore_patterns=["dist/"]))
        names = [c.name for c in tree.children]
        assert "dist" not in names
        assert "dist.py" in names  # a file must not be caught by dist/


class TestFilesOnlyPruning:
    """--files-only must hide directories with no files anywhere below them."""

    def test_dir_holding_only_empty_dirs_is_hidden(self, tmp_path):
        (tmp_path / "real").mkdir()
        (tmp_path / "real" / "x.py").write_text("")
        (tmp_path / "onlyempty").mkdir()
        (tmp_path / "onlyempty" / "inner").mkdir()

        names = _collect_names(build_tree(tmp_path, TreeOptions(files_only=True)))
        assert "onlyempty" not in names
        assert "inner" not in names
        assert "real" in names
        assert "x.py" in names

    def test_dir_holding_only_ignored_files_is_hidden(self, tmp_path):
        (tmp_path / "logs").mkdir()
        (tmp_path / "logs" / "debug.log").write_text("")

        tree = build_tree(tmp_path, TreeOptions(files_only=True, ignore_patterns=["*.log"]))
        assert "logs" not in _collect_names(tree)

    def test_ancestor_of_deep_file_is_kept(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "c").mkdir()
        (tmp_path / "a" / "b" / "c" / "deep.txt").write_text("")

        names = _collect_names(build_tree(tmp_path, TreeOptions(files_only=True)))
        assert "a" in names and "b" in names and "c" in names and "deep.txt" in names

    def test_files_only_respects_depth_limit(self, tmp_path):
        """A directory whose only contents fall beyond --depth is pruned.

        Nothing under a/ is reachable at depth 1, so showing it would render a
        misleading empty leaf.
        """
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "deep.txt").write_text("")

        tree = build_tree(tmp_path, TreeOptions(files_only=True, depth=1))
        assert [c.name for c in tree.children] == []

    def test_files_only_keeps_ancestors_within_depth(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "b").mkdir()
        (tmp_path / "a" / "b" / "deep.txt").write_text("")

        names = _collect_names(build_tree(tmp_path, TreeOptions(files_only=True, depth=3)))
        assert "a" in names and "b" in names and "deep.txt" in names


class TestSymlinkClassification:
    """Symlinked directories must be classified as directories.

    ``is_symlink()`` is faked so these run on Windows too, where creating real
    symlinks needs elevated privileges.
    """

    def _setup(self, tmp_path, monkeypatch, name="linkdir"):
        (tmp_path / "realdir").mkdir()
        (tmp_path / "realdir" / "a.txt").write_text("")
        (tmp_path / name).mkdir()
        (tmp_path / name).joinpath("inner.txt").write_text("")
        (tmp_path / "file.txt").write_text("")

        original = Path.is_symlink
        monkeypatch.setattr(
            Path, "is_symlink", lambda self: True if self.name == name else original(self)
        )

    def test_symlinked_dir_is_a_dir_and_is_not_followed(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch)
        tree = build_tree(tmp_path, TreeOptions())
        link = next(c for c in tree.children if c.name == "linkdir")
        assert link.is_dir is True
        assert link.is_symlink is True
        assert link.children == []

    def test_symlinked_dir_sorted_after_real_dirs_before_files(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch)
        names = [c.name for c in build_tree(tmp_path, TreeOptions()).children]
        assert names == ["realdir", "linkdir", "file.txt"]

    def test_symlinked_dir_shown_under_dirs_only(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch)
        names = [c.name for c in build_tree(tmp_path, TreeOptions(dirs_only=True)).children]
        assert "linkdir" in names
        assert "file.txt" not in names

    def test_symlinked_dir_hidden_under_files_only(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch)
        assert "linkdir" not in _collect_names(build_tree(tmp_path, TreeOptions(files_only=True)))

    def test_symlinked_dir_rendered_with_trailing_slash(self, tmp_path, monkeypatch):
        from treemark.output import render_tree

        self._setup(tmp_path, monkeypatch)
        out = render_tree(build_tree(tmp_path, TreeOptions()))
        assert "linkdir/ -> (symlink)" in out

    def test_symlink_to_file_behaves_like_a_file(self, tmp_path, monkeypatch):
        (tmp_path / "realfile.txt").write_text("")
        (tmp_path / "link.txt").write_text("")
        original = Path.is_symlink
        monkeypatch.setattr(
            Path, "is_symlink", lambda self: True if self.name == "link.txt" else original(self)
        )

        names = [c.name for c in build_tree(tmp_path, TreeOptions(dirs_only=True)).children]
        assert "link.txt" not in names  # dirs-only hides files, symlinked files included

        names = [c.name for c in build_tree(tmp_path, TreeOptions()).children]
        assert "link.txt" in names
