"""Tests for CLI argument parsing and end-to-end behavior."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from treemark.cli import _prefer_utf8_streams, main


class TestCLIBasic:
    def test_cli_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "treemark" in captured.out.lower()

    def test_cli_version(self, capsys):
        from treemark import __version__

        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out

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


class TestCLIMutuallyExclusiveModes:
    def test_files_only_with_dirs_only_rejected(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["--files-only", "--dirs-only", str(tmp_path)])
        assert exc_info.value.code != 0

    def test_files_only_with_no_files_rejected(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            main(["--files-only", "--no-files", str(tmp_path)])
        assert exc_info.value.code != 0

    def test_dirs_only_with_no_files_allowed(self, tmp_path, capsys):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("")
        main(["--dirs-only", "--no-files", str(tmp_path)])
        assert "src" in capsys.readouterr().out

    def test_error_message_mentions_both_flags(self, tmp_path, capsys):
        with pytest.raises(SystemExit):
            main(["--files-only", "--dirs-only", str(tmp_path)])
        captured = capsys.readouterr()
        assert "--files-only" in captured.err


class TestPreferUtf8Streams:
    """Redirected output used to fall back to a legacy code page on Windows,
    which replaced box-drawing characters and emoji with '?'."""

    def test_reconfigures_streams_that_support_it(self, monkeypatch):
        class Recorder:
            def __init__(self):
                self.calls = []

            def reconfigure(self, **kwargs):
                self.calls.append(kwargs)

        out, err = Recorder(), Recorder()
        monkeypatch.setattr("treemark.cli.sys.stdout", out)
        monkeypatch.setattr("treemark.cli.sys.stderr", err)

        _prefer_utf8_streams()

        expected = [{"encoding": "utf-8", "errors": "replace"}]
        assert out.calls == expected
        assert err.calls == expected

    def test_streams_without_reconfigure_are_left_alone(self, monkeypatch):
        class Bare:
            pass

        monkeypatch.setattr("treemark.cli.sys.stdout", Bare())
        monkeypatch.setattr("treemark.cli.sys.stderr", Bare())
        _prefer_utf8_streams()  # must not raise

    def test_reconfigure_failure_is_swallowed(self, monkeypatch):
        class Closed:
            def reconfigure(self, **kwargs):
                raise ValueError("I/O operation on closed file")

        monkeypatch.setattr("treemark.cli.sys.stdout", Closed())
        monkeypatch.setattr("treemark.cli.sys.stderr", Closed())
        _prefer_utf8_streams()  # must not raise


class TestCLIRootLabel:
    def test_root_label_ends_with_slash(self, tmp_path, capsys):
        (tmp_path / "a.txt").write_text("")
        main([str(tmp_path)])
        first = capsys.readouterr().out.split("\n", 1)[0]
        # resolve() may realign the path (e.g. /var -> /private/var on macOS)
        expected = tmp_path.resolve().name
        assert first == f"{expected}/"

    def test_root_label_is_a_directory(self, tmp_path, capsys):
        """Scanning a real subdirectory must label it with its own name."""
        (tmp_path / "project").mkdir()
        (tmp_path / "project" / "a.txt").write_text("")
        main([str(tmp_path / "project")])
        first = capsys.readouterr().out.split("\n", 1)[0]
        assert first == "project/"
