# Changelog

All notable changes to TreeMark are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-19

### Fixed

- **Ignore path patterns were depth-dependent.** Patterns were matched against a
  path relative to the *parent of the directory being walked*, so `a/b/c.txt`
  matched at some nesting levels and silently failed at others. Patterns are now
  always relative to the scan root.
- **Ignore matching no longer depends on the host OS.** `fnmatch.fnmatch` folds
  case on Windows but not on macOS/Linux, so the same `.treeignore` behaved
  differently per platform. Matching now uses `fnmatch.fnmatchcase`.
- **`--files-only` kept directories with no files.** A directory holding only
  other (empty) directories was still shown. Such directories are now pruned,
  including when a `--depth` limit hides every file below them.
- **Symlinked directories were misclassified as files.** The directory branch
  was unreachable because symlinks had their forced `is_dir` to `False` first,
  so symlinked directories rendered without a trailing slash, appeared before
  real directories, and were excluded by `--dirs-only`. They are now shown as
  directories (marked `-> (symlink)`), sorted with other directories, and still
  never followed.
- **`docker-compose.yml` never got its emoji.** The `.yml` rule matched before
  the special-filename rule could run. Special names are now checked first.
- **Markdown fence could be broken by a file name.** The fence was a fixed five
  backticks, which a longer backtick run would escape. It is now sized to the
  content (minimum three).
- **Emoji on a redirected console produced raw bytes.** The Unicode fallback
  wrote UTF-8 bytes straight to the underlying buffer, which displayed as
  mojibake. It now falls back to readable replacement characters, and stdout
  and stderr are reconfigured to UTF-8 when redirected so box-drawing characters
  and emoji survive on Windows.
- **Scanning a filesystem root** (`/` or `C:\`) produced a malformed header.
- Unreadable directories other than `PermissionError` (e.g. `OSError`) now warn
  instead of crashing.

### Added

- Trailing-slash ignore patterns (`dist/`) now match directories only, following
  the gitignore convention.
- `.treeignore` patterns in the built-in default list may now be globs.
- `--files-only` and `--dirs-only`/`--no-files` are now rejected together
  instead of silently letting `--dirs-only` win.
- Recognized emoji file types expanded to cover Go, Rust, Java, Kotlin, C/C++,
  C#, Ruby, PHP, Swift, SQL, shell scripts, images, archives, and more.
- `Makefile`/`GNUmakefile` now map to an emoji, case-insensitively.
- `.gitignore`, and removal of the accidentally committed `__pycache__/` and
  `*.egg-info/` build artifacts.
- `requirements-dev.txt` (test dependencies; runtime remains standard library only).
- Python 3.13 and 3.14 classifiers; corrected repository URLs.

### Changed

- Built-in default ignores now also cover `.ruff_cache`, `.tox`, `.nox`,
  `.eggs`, `*.egg-info`, `.idea`, and `.vscode`.
- Warning messages for unreadable directories now include the OS error detail.

## [0.1.0]

Initial release.

[0.2.0]: https://github.com/kritagyadubey/TreeMark/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kritagyadubey/TreeMark/releases/tag/v0.1.0
