"""Tests for CLI argument parsing and end-to-end behavior."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from treemark.cli import main


class TestCLIBasic:
    def test_cli_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "treemark" in captured.out.lower()

    def test_cli_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "0.1.0" in captured.out

    def test_cli_default_directory(self, tmp_path, capsys):
        (tmp_path / "file.txt").write_text("")
        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            main([])
        finally:
            os.chdir(old_cwd)
        captured = capsys.readouterr()
        assert "file.txt" in captured.out

    def test_cli_explicit_path(self, tmp_path, capsys):
        (tmp_path / "hello.py").write_text("")
        main(["--output", str(tmp_path / "out.md"), str(tmp_path)])
        output_file = tmp_path / "out.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "hello.py" in content


class TestCLIDepth:
    def test_depth_zero(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--depth", "0", str(tmp_path)])
        captured = capsys.readouterr()
        assert "main.py" not in captured.out

    def test_negative_depth(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--depth", "-1"])
        assert exc_info.value.code != 0


class TestCLIAll:
    def test_all_flag(self, tmp_path, capsys):
        (tmp_path / ".env").write_text("")
        (tmp_path / "visible.txt").write_text("")
        main(["--all", str(tmp_path)])
        captured = capsys.readouterr()
        assert ".env" in captured.out
        assert "visible.txt" in captured.out


class TestCLIFilesOnly:
    def test_files_only(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        (tmp_path / "empty_dir").mkdir()
        main(["--files-only", str(tmp_path)])
        captured = capsys.readouterr()
        assert "empty_dir" not in captured.out
        assert "main.py" in captured.out


class TestCLIDirsOnly:
    def test_dirs_only(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--dirs-only", str(tmp_path)])
        captured = capsys.readouterr()
        assert "main.py" not in captured.out
        assert "src" in captured.out


class TestCLINoFiles:
    def test_no_files(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--no-files", str(tmp_path)])
        captured = capsys.readouterr()
        assert "main.py" not in captured.out


class TestCLIIgnore:
    def test_ignore_comma_separated(self, tmp_path, capsys):
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "dist").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--ignore", "node_modules,dist", str(tmp_path)])
        captured = capsys.readouterr()
        assert "node_modules" not in captured.out
        assert "dist" not in captured.out

    def test_ignore_repeated(self, tmp_path, capsys):
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "dist").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--ignore", "node_modules", "--ignore", "dist", str(tmp_path)])
        captured = capsys.readouterr()
        assert "node_modules" not in captured.out
        assert "dist" not in captured.out


class TestCLIIgnoreFile:
    def test_explicit_ignore_file(self, tmp_path, capsys):
        gi = tmp_path / "custom.ignore"
        gi.write_text("secret\n")
        (tmp_path / "secret").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--ignore-file", str(gi), str(tmp_path)])
        captured = capsys.readouterr()
        assert "secret" not in captured.out

    def test_auto_treeignore(self, tmp_path, capsys):
        gi = tmp_path / ".treeignore"
        gi.write_text("secret\n")
        (tmp_path / "secret").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main([str(tmp_path)])
        captured = capsys.readouterr()
        assert "secret" not in captured.out

    def test_missing_explicit_ignore_file(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["--ignore-file", str(tmp_path / "nonexistent"), str(tmp_path)])
        assert exc_info.value.code != 0


class TestCLINoDefaultIgnore:
    def test_no_default_ignore(self, tmp_path, capsys):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--no-default-ignore", "--all", str(tmp_path)])
        captured = capsys.readouterr()
        assert ".git" in captured.out


class TestCLIMarkdown:
    def test_markdown_output(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--markdown", str(tmp_path)])
        captured = capsys.readouterr()
        assert captured.out.startswith("```text\n")
        assert captured.out.strip().endswith("```")


class TestCLIAscii:
    def test_ascii_output(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--ascii", str(tmp_path)])
        captured = capsys.readouterr()
        assert "+-- " in captured.out or "\\-- " in captured.out


class TestCLIEmoji:
    def test_emoji_output(self, tmp_path, capsys):
        (tmp_path / "main.py").write_text("")
        main(["--emoji", str(tmp_path)])
        captured = capsys.readouterr()
        assert "\U0001f40d" in captured.out  # snake emoji


class TestCLIOutput:
    def test_output_file(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        out = tmp_path / "tree.md"
        main(["--output", str(out), str(tmp_path)])
        assert out.exists()
        content = out.read_text()
        assert "main.py" in content

    def test_output_file_inside_scan_root_excludes_itself(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        # Create an existing tree.md that should be excluded
        (tmp_path / "tree.md").write_text("old content")
        out = tmp_path / "tree.md"
        main(["--output", str(out), str(tmp_path)])
        content = out.read_text()
        # tree.md should NOT appear in the output tree
        lines = content.strip().split("\n")
        for line in lines[1:]:  # skip root line
            assert "tree.md" not in line


class TestCLIInvalidPath:
    def test_invalid_path(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["/nonexistent/path"])
        assert exc_info.value.code != 0


class TestModuleExecution:
    def test_module_run(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "treemark", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "treemark" in result.stdout.lower()


class TestCLIPrivate:
    def test_plain_flag(self, tmp_path, capsys):
        (tmp_path / "file.txt").write_text("")
        main(["--plain", str(tmp_path)])
        captured = capsys.readouterr()
        assert "file.txt" in captured.out
