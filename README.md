# TreeMark

Generate clean project trees for Markdown, READMEs, docs, and terminals.

## Why TreeMark

You're writing a README and need a project tree. You could manually type it out, or use a tool that prints noisy output you don't want. TreeMark does one thing well: it scans a directory and prints a clean, readable tree you can paste straight into a Markdown file.

- Zero runtime dependencies
- Works on Windows, macOS, and Linux
- Outputs plain text, Markdown, or ASCII
- Ignores common junk by default (`.git`, `node_modules`, `__pycache__`)
- Respects `.treeignore` files

## Installation

```bash
pip install treemark
```

Or install from source:

```bash
git clone https://github.com/kritagyadubey/treemark.git
cd treemark
pip install -e .
```

## Quick Start

```bash
cd my-project
treemark
```

Output:

```
my-project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── README.md
└── pyproject.toml
```

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
- Patterns are checked against the entry name and its relative path
- Negation patterns (`!foo`) are not supported

You can use `--ignore-file` to specify a custom ignore file, or `--no-default-ignore` to disable the built-in ignore list entirely.

## Markdown Output

```bash
treemark --markdown
```

This wraps the tree in a fenced code block:

````markdown
```text
my-project/
├── src/
│   └── main.py
└── README.md
```
````

Copy the output directly into your README. The fence automatically uses a longer delimiter if the tree itself contains triple backticks.

## Emoji Mode

```bash
treemark --emoji
```

Adds small emojis for common file types:

- `.py` files
- `.js` / `.ts` / `.html` / `.css` files
- `.json` / `.md` / `.yml` / `.yaml` / `.toml` files
- `Dockerfile`

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
git clone https://github.com/kritagyadubey/treemark.git
cd treemark
pip install -e .
```

## Testing

```bash
pytest
```

## Contributing

Contributions are welcome. Keep things simple. If you're adding a feature, add a test for it.

## Privacy

TreeMark runs entirely on your local machine. It:

- Does not upload files
- Does not upload directory listings
- Does not make network requests
- Does not send telemetry
- Does not collect analytics
- Does not require an internet connection

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

**Kritagya Dubey**

GitHub: [@kritagyadubey](https://github.com/kritagyadubey)
