# TreeMark

[![PyPI version](https://img.shields.io/pypi/v/treemark.svg)](https://pypi.org/project/treemark/)
[![Python versions](https://img.shields.io/pypi/pyversions/treemark.svg)](https://pypi.org/project/treemark/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)](#installation)

Generate clean project trees for Markdown, READMEs, docs, and terminals.

## Why TreeMark

You're writing a README and need a project tree. You could manually type it out, or use a tool that prints noisy output you don't want. TreeMark does one thing well: it scans a directory and prints a clean, readable tree you can paste straight into a Markdown file.

- Zero runtime dependencies
- Works on Windows, macOS, and Linux
- Outputs plain text, Markdown, or ASCII
- Ignores common junk by default (`.git`, `node_modules`, `__pycache__`, `*.egg-info`)
- Respects `.treeignore` files
- Ignore rules match the same way on every platform

## Installation

Requires Python 3.10 or newer. No runtime dependencies.

```bash
pip install treemark
```

Or install from source:

```bash
git clone https://github.com/kritagyadubey/TreeMark.git
cd TreeMark
pip install -e .
```

## Quick Start

Run TreeMark on this repository to see it produce a real tree:

```bash
treemark --markdown
```

Output:

```text
treemark/
├── src/
│   └── treemark/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── ignore.py
│       ├── output.py
│       └── tree.py
├── tests/
│   ├── test_cli.py
│   ├── test_ignore.py
│   ├── test_output.py
│   └── test_tree.py
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements-dev.txt
```

Build output such as `__pycache__/` and `*.egg-info/` is ignored by default, so
there is nothing to clean up before running it on a working checkout.

## Examples

Scan a specific directory:

```bash
treemark path/to/project
```

Limit depth to 2 levels:

```bash
treemark --depth 2
```

Include hidden files:

```bash
treemark --all
```

Show only files:

```bash
treemark --files-only
```

Show only directories:

```bash
treemark --dirs-only
```

Ignore specific patterns:

```bash
treemark --ignore "node_modules,dist,*.log"
```

Disable built-in ignores:

```bash
treemark --no-default-ignore
```

Use ASCII tree characters:

```bash
treemark --ascii
```

Show file type emojis:

```bash
treemark --emoji
```

Write output to a file:

```bash
treemark --output tree.md
```

## Options

| Option | Description |
|---|---|
| `path` | Directory to scan (default: current directory) |
| `--depth N` | Maximum depth to scan (default: unlimited) |
| `--all`, `-a` | Include hidden files and directories |
| `--files-only` | Show only files |
| `--dirs-only` | Show only directories |
| `--no-files` | Alias for `--dirs-only` |
| `--ignore PATTERNS` | Comma-separated patterns to ignore (may be repeated) |
| `--ignore-file FILE` | Path to ignore file (default: auto-load `.treeignore` if present) |
| `--no-default-ignore` | Disable built-in default ignore patterns |
| `--markdown`, `-m` | Output as a Markdown fenced code block |
| `--plain` | Output plain tree (default) |
| `--emoji` | Show emojis for common file types |
| `--ascii` | Use ASCII tree characters instead of Unicode |
| `--output FILE`, `-o` | Write output to a file instead of stdout |
| `--version`, `-v` | Show version |
| `--help`, `-h` | Show help |

`--files-only` and `--dirs-only` (or its `--no-files` alias) are mutually
exclusive; combining them is an error rather than a silent winner.

## .treeignore

TreeMark supports `.treeignore` files. If a `.treeignore` file exists in the directory you're scanning, it will be loaded automatically.

Example `.treeignore`:

```
node_modules
dist
*.log
data/*.csv
```

Rules:

- Blank lines are ignored
- Lines starting with `#` are comments
- Exact names are supported
- Glob patterns (`*.log`, `test_*`) work via `fnmatch`
- Patterns are checked against the entry name and its path relative to the
  directory you are scanning, so `data/*.csv` matches the same entry at any
  nesting level
- Matching is **case-sensitive on every platform**; a `.treeignore` behaves the
  same on Windows, macOS and Linux
- A trailing `/` matches directories only: `dist/` ignores the `dist` directory
  but not a `dist.py` file
- Negation patterns (`!foo`) are not supported

You can use `--ignore-file` to specify a custom ignore file, or `--no-default-ignore` to disable the built-in ignore list entirely.

### Default ignores

Unless `--no-default-ignore` is set, these names are ignored automatically:

```
.git            node_modules    __pycache__     .venv
venv            env             dist            build
.cache          .mypy_cache     .pytest_cache   .ruff_cache
.tox            .nox            .eggs           *.egg-info
.idea           .vscode
```

## Markdown Output

```bash
treemark --markdown
```

This wraps the tree in a fenced code block. Running `treemark --markdown --depth 2` on this repository:

````markdown
```text
treemark/
├── src/
│   └── treemark/
├── tests/
│   ├── test_cli.py
│   ├── test_ignore.py
│   ├── test_output.py
│   └── test_tree.py
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements-dev.txt
```
````

Copy the output directly into your README. The fence is sized to its content —
it grows to one backtick longer than the longest backtick run inside the tree,
so a file name containing backticks can never break out of the block.

## Emoji Mode

```bash
treemark --emoji
```

Adds small emojis for common file types. This repository rendered with emojis
(same tree as Quick Start):

```text
treemark/
├── 📁 src/
│   └── 📁 treemark/
│       ├── 🐍 __init__.py
│       ├── 🐍 __main__.py
│       ├── 🐍 cli.py
│       ├── 🐍 ignore.py
│       ├── 🐍 output.py
│       └── 🐍 tree.py
├── 📁 tests/
│   ├── 🐍 test_cli.py
│   ├── 🐍 test_ignore.py
│   ├── 🐍 test_output.py
│   └── 🐍 test_tree.py
├── 📝 CHANGELOG.md
├── LICENSE
├── ⚙️ pyproject.toml
├── 📝 README.md
└── 📄 requirements-dev.txt
```

Recognized file types:

- **Python** `.py`
- **JavaScript / TypeScript** `.js` `.jsx` `.ts` `.tsx` `.vue` `.svelte`
- **Web** `.html` `.css` `.scss`
- **Markup & config** `.json` `.md` `.rst` `.txt` `.yml` `.yaml` `.toml` `.ini` `.cfg` `.conf` `.xml` `.lock`
- **Shell** `.sh` `.bash` `.zsh` `.ps1` `.bat` `.cmd`
- **Systems & compiled** `.go` `.rs` `.c` `.h` `.cpp` `.hpp` `.cs`
- **Other languages** `.java` `.kt` `.swift` `.rb` `.php` `.lua` `.r` `.sql` `.ipynb`
- **Images & archives** `.png` `.jpg` `.jpeg` `.gif` `.svg` `.ico` `.zip` `.gz` `.tar`
- **Logs** `.log`
- **Special names** `Dockerfile`, `docker-compose.yml`, `docker-compose.yaml`, `Makefile`, `GNUmakefile`

Emoji mode only affects display. It does not change sorting, ignore behavior, or path handling.

## Output to File

```bash
treemark --output tree.md
```

If the output file is inside the scanned directory, it will be automatically excluded from the tree. Parent directories for the output file are created if they don't exist.

## Running as a Module

```bash
python -m treemark
```

## Development

Clone and install in development mode:

```bash
git clone https://github.com/kritagyadubey/TreeMark.git
cd TreeMark
pip install -e .
```

## Testing

Install the test dependencies and run the suite:

```bash
pip install -r requirements-dev.txt
pytest
```

TreeMark has no third-party runtime dependencies, so `requirements-dev.txt`
only lists the test runner. The suite covers tree building, sorting, depth
limits, ignore matching, symlink handling, output formatting, and the CLI.

## Known Limitations

- Symlinked directories are shown in the tree but not scanned; they are marked with `-> (symlink)` and treated as leaves.
- Only a `.treeignore` in the directory being scanned is loaded automatically. Nested `.treeignore` files in subdirectories are not applied.

## Contributing

Contributions are welcome. Keep things simple. If you're adding a feature, add a test for it.

- Report bugs and suggest features in [GitHub Issues](https://github.com/kritagyadubey/TreeMark/issues). Include your OS, Python version, the command you ran, and what you expected versus what you got.
- Open a pull request from a fork. Keep changes small and focused.
- Run the test suite before submitting: `pytest` (run it from the repository root after `pip install -e .`).
- By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).

## Privacy

TreeMark runs entirely on your local machine. It:

- Does not upload files
- Does not upload directory listings
- Does not make network requests
- Does not send telemetry
- Does not collect analytics
- Does not require an internet connection

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full list of changes.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

**Kritagya Dubey**

GitHub: [@kritagyadubey](https://github.com/kritagyadubey)
