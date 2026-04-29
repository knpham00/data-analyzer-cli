# AGENTS.md — How AI Helped Build This

This project was built with [Claude Code](https://claude.ai/code) (Anthropic), an AI coding assistant embedded in the development workflow. This document describes the collaboration honestly.

## What the AI built

The AI generated the full initial implementation of this project in a single session:

- **`analyzer.py`** — the complete CLI tool including argument parsing, CSV loading, type inference, stats computation, missing-value counting, and error handling
- **`tests/test_analyzer.py`** — a pytest suite with 20+ assertions across 4 test classes
- **`.github/workflows/ci.yml`** — a GitHub Actions workflow running tests on Python 3.9–3.12 with a separate ruff lint job
- **`README.md`** — usage documentation with examples, error reference table, and project structure
- **`AGENTS.md`** — this file

In a follow-up session, the AI added Rich terminal output across the entire project:

- **`analyzer.py`** — replaced all plain `print()` calls with Rich Panels and Tables; added colored type labels, red/green missing-value highlighting, and bold red error messages via a dedicated stderr console
- **`tests/test_analyzer.py`** — updated integration tests to inject a `StringIO`-backed `RichConsole` for output capture; added 3 new integration tests (26 total); removed `match=` from error tests since errors now exit with code `1` rather than a message string
- **`requirements.txt`** — new file declaring `rich` as the sole dependency
- **`.github/workflows/ci.yml`** — updated install step to `pip install -r requirements.txt pytest` so Rich is available on CI

In a third session, the AI added the `--export` flag:

- **`analyzer.py`** — added `_write_export`, `export_summary`, `export_column`, and `export_missing` functions that write plain CSV output (no Rich markup) to disk; added `--export FILE` argument to `main()` that calls the appropriate export function after displaying terminal output, with a green success message and a guard that errors if multiple data flags are combined with `--export`
- **`tests/test_analyzer.py`** — added `TestExport` class with 6 tests covering file creation, CSV content correctness for all three export types, and the multiple-flags error case (32 tests total)

## Prompts used
- *"explain each function in analyzer.py in simple terms"* — used to get a plain-English summary of every function, which informed the decision to add `--export` and Rich styling

- *"Build me a Python CLI CSV data analyzer called analyzer.py. 
It should:
- Accept a CSV file as input
- Have a --summary flag that shows row count, column names, and data types
- Have a --column flag that shows min, max, and average for a numeric column
- Have a --missing flag that shows count of missing values per column
- Handle bad input gracefully with helpful error messages
- Use only Python built-in libraries (no pandas)
- Include at least 5 pytest tests in a tests/ folder
- Include a GitHub Actions workflow in .github/workflows/ci.yml that runs the tests
- Include a thorough README.md
- Include an AGENTS.md describing how AI helped build this"*

- *"Add the Rich library to the project to make all terminal output prettier. 
Use tables, colors, and panels where appropriate:
- --summary should show a styled table with row count, column names, and data types
- --column should show a styled panel with min, max, and average
- --missing should show a styled table with missing value counts per column
- Error messages should show in red
- Success output should show in green
Also add rich to a requirements.txt file so it can be installed with pip.
Update the GitHub Actions workflow to install requirements.txt before running tests."*

- *"Add a --export flag to analyzer.py that saves the current 
command's output to a CSV file. It should work alongside 
any existing flag like --summary, --column, or --missing. 
Still show the Rich output in the terminal as normal, and 
print a green success message showing the filename it was 
saved to. Add at least 2 pytest tests for the export feature."*

### Session 1 — initial build

The project was generated from a single structured prompt specifying:

- Accept a CSV file as input
- `--summary`: row count, column names, data types
- `--column`: min/max/average for a numeric column
- `--missing`: missing values per column
- Graceful error handling
- Built-in Python libraries only (no pandas)
- At least 5 pytest tests
- GitHub Actions CI workflow
- README and AGENTS docs

### Session 2 — Rich output

> Add the Rich library to the project to make all terminal output prettier. Use tables, colors, and panels where appropriate: `--summary` should show a styled table with row count, column names, and data types; `--column` should show a styled panel with min, max, and average; `--missing` should show a styled table with missing value counts per column. Error messages should show in red. Success output should show in green. Also add rich to a requirements.txt file so it can be installed with pip. Update the GitHub Actions workflow to install requirements.txt before running tests.

### Session 3 — `--export` flag

> Add a `--export` flag to analyzer.py that saves the current command's output to a CSV file. It should work alongside any existing flag like `--summary`, `--column`, or `--missing`. Still show the Rich output in the terminal as normal, and print a green success message showing the filename it was saved to. Add at least 2 pytest tests for the export feature.

## Design decisions made by the AI

- **Type inference via sequential parsing** — the AI chose to attempt `int` parsing first, then `float`, then fall back to `string`, rather than using regex or a heuristic. This keeps the logic simple and dependency-free.
- **`sys.exit()` for user-facing errors** — rather than raising exceptions and catching them in `main()`, errors that indicate bad user input call `sys.exit()` directly. This keeps error paths short and avoids boilerplate.
- **Skipping blank values in `--column`** — the AI decided that missing values should be excluded from numeric stats and counted separately, matching common data analysis conventions.
- **`_fmt_num` helper** — to avoid printing `82.0` for what is clearly an integer, the AI added a small formatter that drops the `.0` suffix when the float is whole.
- **Combined flags** — the AI separated display logic (`cmd_summary`, `cmd_column`, `cmd_missing`) from computation logic (`get_summary`, `get_column_stats`, `get_missing_counts`) so that flags could be combined freely and each function could be tested independently.

## What the AI did not do

- The AI did not run the tests during the initial generation (no shell access at that point). Tests were written based on the author's understanding of the implementation and standard pytest patterns — one test had a wrong expected value and was corrected after running the suite locally.
- The AI did not choose the project name, repository structure beyond what was specified, or make assumptions about deployment environment.
- No AI-generated code in session 1 uses third-party libraries — the stdlib-only constraint was respected. Rich was added in session 2 only after the user explicitly requested it.
- The AI did not decide which features to build. I read through every function in `analyzer.py`, added comments above each one to understand what the code was doing, and then decided which features to add (Rich styling, `--export` flag) before prompting the AI to implement them.
- The AI did not manually test the features. I personally tested every feature in the terminal, including:
  - `python3 analyzer.py test_data.csv --summary --export results.csv`
  - `python3 analyzer.py test_data.csv --missing --export missing_results.csv`
  - `python3 analyzer.py test_data.csv --column age --export age_results.csv`
  - `python3 analyzer.py fake.csv --export results.csv` (file not found edge case)
  - `python3 analyzer.py test_data.csv` (no flags edge case)
  - Verified each exported CSV file opened correctly and contained the right data

## Verification

After generation, the tests should be run locally and on CI to confirm correctness:

```bash
pip install pytest
pytest tests/ -v
```

Any failures indicate a divergence between the implementation and the test expectations and should be investigated before merging.
