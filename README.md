# CSV Data Analyzer

A command-line tool for exploring CSV files with styled terminal output. Uses only Python built-ins plus [Rich](https://github.com/Textualize/rich) for formatting.

## What it does

Point it at any CSV file and use flags to instantly understand your data:

- **`--summary`** — see row count, column names, and inferred data types
- **`--column COLUMN`** — get min, max, and average for any numeric column
- **`--missing`** — find which columns have blank values and how many
- **`--export FILE`** — save any result to a new CSV file

All output is styled with colors and tables in the terminal. Errors appear in bold red with a helpful message explaining what went wrong.

## Requirements

- Python 3.9 or newer
- pip (comes with Python)

Check your Python version:
```bash
python3 --version
```

## Installation

```bash
git clone https://github.com/knpham00/data-analyzer-cli.git
cd data-analyzer-cli
pip install -r requirements.txt
```

Verify it works:
```bash
python3 analyzer.py --help
```

You should see:
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

## Usage

All commands follow this pattern:
```bash
python3 analyzer.py YOUR_FILE.csv --flag
```

---

### `--summary`

Shows the total number of rows and columns, and the inferred data type for each column.

```bash
python3 analyzer.py data.csv --summary
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

Types are color-coded: **cyan** for integer, **yellow** for float, **white** for string.

---

### `--column COLUMN`

Shows the count, minimum, maximum, and average for a numeric column. Replace `COLUMN` with the exact column name.

```bash
python3 analyzer.py data.csv --column salary
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

Blank cells are skipped — they are not counted as zero.

---

### `--missing`

Shows how many blank cells each column has. Useful for spotting incomplete data before analysis.

```bash
python3 analyzer.py data.csv --missing
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

Counts above zero appear in **red**. Zero counts appear in **green**.

---

### `--export FILE`

Saves the result to a plain CSV file — no colors or formatting, just data. Use it alongside one data flag.

```bash
python3 analyzer.py data.csv --summary --export summary.csv
```
```
╭─── Summary ───╮
│ 1000 rows · 5 columns │
╰───────────────╯
... (table shown in terminal as normal) ...

✓ Exported to summary.csv
```

The exported `summary.csv` will contain:
```
column,type
id,integer
name,string
age,integer
salary,float
department,string
```

Works with all three data flags:
```bash
python3 analyzer.py data.csv --column salary --export salary_stats.csv
python3 analyzer.py data.csv --missing --export missing.csv
```

---

### Combining flags

`--summary` and `--missing` can be combined in one command:

```bash
python3 analyzer.py data.csv --summary --missing
```
```
╭─── Summary ───╮
│ 1000 rows · 5 columns │
╰───────────────╯
╭──────────────────────┬──────────╮
│ Column               │ Type     │
...
╰──────────────────────┴──────────╯

╭──────────────────────┬─────────╮
│ Column               │ Missing │
...
╰──────────────────────┴─────────╯

Total missing values: 9
```

Note: `--export` can only be used with one data flag at a time.

---

## Error handling

All errors print in bold red and exit with a helpful message. No tracebacks.

| Situation | Message |
|-----------|---------|
| File not found | `Error: File 'x.csv' not found.` |
| Wrong file extension | `Error: 'x.txt' is not a CSV file.` |
| Empty file | `Error: CSV file is empty or has no header row.` |
| Column name doesn't exist | `Error: Column 'x' not found. Available columns: …` |
| Column contains text, not numbers | `Error: Column 'name' contains non-numeric value 'Alice' at row 2.` |
| Column is entirely blank | `Error: Column 'x' has no numeric values.` |
| File uses non-UTF-8 encoding | `Error: Could not decode file. Ensure it is UTF-8 encoded.` |
| `--export` used without a data flag | `Error: --export requires a data flag.` |
| `--export` used with multiple data flags | `Error: --export requires exactly one data flag.` |
| Export path doesn't exist | `Error: Could not write to 'path/out.csv': No such file or directory.` |

## Running tests

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

The test suite (34 tests) covers:

- CSV loading — headers, rows, missing file, wrong extension, empty file
- Summary — row count, column names, type inference for integer/float/string
- Column stats — min, max, average, blank-cell exclusion, edge cases
- Missing value counts — per-column accuracy, all-blank columns, whitespace cells
- Export — file creation, CSV content for all three export types, error cases
- CLI output — correct display for each flag

## Project structure

```
data-analyzer-cli/
├── analyzer.py               # Main CLI tool
├── requirements.txt          # Python dependencies (rich)
├── tests/
│   └── test_analyzer.py      # Pytest test suite (34 tests)
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI
├── README.md
└── AGENTS.md
```

## CI

GitHub Actions runs the full test suite on Python 3.9, 3.10, 3.11, and 3.12 on every push and pull request. A separate lint job runs [ruff](https://docs.astral.sh/ruff/) for style checks. No manual steps are needed — all checks run automatically.

## License

MIT
