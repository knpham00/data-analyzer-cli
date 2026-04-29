# CSV Data Analyzer

A command-line tool for exploring CSV files with styled terminal output. Uses only Python built-ins plus [Rich](https://github.com/Textualize/rich) for formatting.

## Features

- **`--summary`** — row count, column names, and inferred data types in a styled table
- **`--column COLUMN`** — min, max, and average for any numeric column in a styled panel
- **`--missing`** — missing value counts per column, color-coded red/green
- **`--export FILE`** — save any command's output to a CSV file
- Flags can be combined in a single invocation
- Error messages displayed in bold red; success messages in green
- Graceful error messages for missing files, bad extensions, non-numeric columns, and encoding issues

## Installation

```bash
git clone https://github.com/your-username/data-analyzer-cli.git
cd data-analyzer-cli
pip install -r requirements.txt
```

## Usage

```
usage: analyzer [-h] [--summary] [--column COLUMN] [--missing] [--export FILE] file

Analyze CSV files from the command line.

positional arguments:
  file             Path to the CSV file

options:
  -h, --help       show this help message and exit
  --summary        Show row count, column names, and inferred data types
  --column COLUMN  Show min, max, and average for a numeric column
  --missing        Show count of missing values per column
  --export FILE    Save output data to a CSV file (use with one data flag)
```

### Examples

**Show a summary of the file:**
```bash
python analyzer.py data.csv --summary
```
```
╭─── Summary ───╮
│ 1000 rows · 5 columns │
╰───────────────╯
╭──────────────────────┬──────────╮
│ Column               │ Type     │
├──────────────────────┼──────────┤
│ id                   │ integer  │
│ name                 │ string   │
│ age                  │ integer  │
│ salary               │ float    │
│ department           │ string   │
╰──────────────────────┴──────────╯
```

**Compute stats for a numeric column:**
```bash
python analyzer.py data.csv --column salary
```
```
╭─── Column: salary ───╮
│ Count    998 numeric values │
│                             │
│ Min      32000              │
│ Max      210000             │
│ Average  78432.15           │
╰─────────────────────────────╯
```

**Find missing values:**
```bash
python analyzer.py data.csv --missing
```
```
╭──────────────────────┬─────────╮
│ Column               │ Missing │
├──────────────────────┼─────────┤
│ id                   │ 0       │
│ name                 │ 0       │
│ age                  │ 2       │
│ salary               │ 2       │
│ department           │ 5       │
╰──────────────────────┴─────────╯

Total missing values: 9
```
*(missing counts appear in red, zeros in green)*

**Export output to a CSV file:**
```bash
python analyzer.py data.csv --summary --export summary.csv
python analyzer.py data.csv --column salary --export salary_stats.csv
python analyzer.py data.csv --missing --export missing.csv
```
```
✓ Exported to summary.csv
```

The exported CSV contains plain data with no formatting — ready to open in Excel or any other tool.

**Combine flags:**
```bash
python analyzer.py data.csv --summary --missing
```

## Error handling

All errors are displayed in bold red. `--export` requires exactly one data flag.

| Situation | Message |
|-----------|---------|
| File not found | `Error: File 'x.csv' not found.` |
| Wrong extension | `Error: 'x.txt' is not a CSV file.` |
| Empty / header-only file | `Error: CSV file is empty or has no header row.` |
| Unknown column | `Error: Column 'x' not found. Available columns: …` |
| Non-numeric column with `--column` | `Error: Column 'name' contains non-numeric value 'Alice' at row 2.` |
| All values missing in column | `Error: Column 'x' has no numeric values.` |
| Non-UTF-8 encoding | `Error: Could not decode file. Ensure it is UTF-8 encoded.` |
| `--export` with multiple data flags | `Error: --export requires exactly one data flag.` |

## Running tests

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

The test suite covers:

- CSV loading (headers, rows, error paths)
- Summary: row count, column names, type inference (string / integer / float)
- Column stats: min, max, average, missing-value exclusion, edge cases
- Missing-value counts: per-column accuracy, all-blank columns
- CLI output format for each flag
- Export: file creation, CSV content correctness for all three export types, multiple-flags error

## Project structure

```
data-analyzer-cli/
├── analyzer.py               # Main CLI tool
├── requirements.txt          # Python dependencies (rich)
├── tests/
│   └── test_analyzer.py      # Pytest test suite (32 tests)
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI
├── README.md
└── AGENTS.md
```

## CI

GitHub Actions runs the test suite on Python 3.9, 3.10, 3.11, and 3.12 on every push and pull request. Dependencies from `requirements.txt` are installed before each run. A separate lint job runs [ruff](https://docs.astral.sh/ruff/) for style checks.

## License

MIT
