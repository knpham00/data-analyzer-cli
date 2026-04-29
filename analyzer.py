#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()
error_console = Console(stderr=True)

_TYPE_COLORS = {"integer": "cyan", "float": "yellow", "string": "white"}


# Prints an error message in bold red to the terminal, then stops the program immediately.
# Called anywhere something goes wrong (bad file, unknown column, etc.).
def _exit_error(msg):
    error_console.print(f"[bold red]Error:[/bold red] {msg}")
    sys.exit(1)


# Opens a CSV file and reads all of its data into memory.
# Checks that the file exists, ends in .csv, and is readable before returning
# two things: a list of column names (headers) and a list of rows (each row is a dictionary).
def load_csv(filepath):
    path = Path(filepath)
    if not path.exists():
        _exit_error(f"File '{filepath}' not found.")
    if path.suffix.lower() != ".csv":
        _exit_error(f"'{filepath}' is not a CSV file.")
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                _exit_error("CSV file is empty or has no header row.")
            headers = list(reader.fieldnames)
            rows = list(reader)
    except UnicodeDecodeError:
        _exit_error("Could not decode file. Ensure it is UTF-8 encoded.")
    if not headers:
        _exit_error("CSV file has no columns.")
    return headers, rows


# Figures out whether a column's values are integers, floats, or plain text.
# Tries integer first, then float, and falls back to string if neither works.
# Blank cells are ignored so they don't affect the result.
def _infer_type(values):
    non_empty = [v for v in values if v.strip() != ""]
    if not non_empty:
        return "string"
    try:
        [int(v) for v in non_empty]
        return "integer"
    except ValueError:
        pass
    try:
        [float(v) for v in non_empty]
        return "float"
    except ValueError:
        pass
    return "string"


# Collects high-level information about the CSV: total row count, column names,
# and the inferred data type for each column. Returns everything as a dictionary.
# This is the data that powers the --summary flag.
def get_summary(headers, rows):
    col_types = {}
    for h in headers:
        values = [row[h] for row in rows]
        col_types[h] = _infer_type(values)
    return {"row_count": len(rows), "columns": headers, "types": col_types}


# Calculates min, max, average, and count for a single numeric column.
# Skips blank cells instead of treating them as zero.
# Exits with a helpful error if the column doesn't exist or contains non-numeric text.
# This is the data that powers the --column flag.
def get_column_stats(headers, rows, column_name):
    if column_name not in headers:
        _exit_error(
            f"Column '{column_name}' not found.\n"
            f"Available columns: {', '.join(headers)}"
        )
    values = []
    for i, row in enumerate(rows, start=2):
        raw = row[column_name].strip()
        if raw == "":
            continue
        try:
            values.append(float(raw))
        except ValueError:
            _exit_error(
                f"Column '{column_name}' contains non-numeric value "
                f"'{raw}' at row {i}."
            )
    if not values:
        _exit_error(f"Column '{column_name}' has no numeric values.")
    return {
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "count": len(values),
    }


# Counts how many cells are blank in each column.
# Returns a dictionary like {"name": 0, "age": 2} so you can see at a glance
# which columns have gaps. This is the data that powers the --missing flag.
def get_missing_counts(headers, rows):
    counts = {}
    for h in headers:
        counts[h] = sum(1 for row in rows if row[h].strip() == "")
    return counts


# Cleans up a number before displaying or exporting it.
# If the value is a whole number (e.g. 82.0), returns it as an integer (82) so it looks cleaner.
# Otherwise rounds to 4 decimal places to avoid long floating point tails.
def _fmt_num(n):
    return int(n) if n == int(n) else round(n, 4)


# Writes a list of dictionaries to a CSV file at the given path.
# Used by all three export functions below as a shared helper.
def _write_export(filepath, export_rows, fieldnames):
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_rows)
    except OSError as e:
        _exit_error(f"Could not write to '{filepath}': {e.strerror}.")


# Saves the --summary data to a CSV file with two columns: "column" and "type".
# One row per column in the original file. Used when --summary and --export are combined.
def export_summary(headers, rows, filepath):
    info = get_summary(headers, rows)
    export_rows = [{"column": col, "type": info["types"][col]} for col in info["columns"]]
    _write_export(filepath, export_rows, ["column", "type"])


# Saves the --column stats to a CSV file with two columns: "stat" and "value".
# Rows are: count, min, max, average. Used when --column and --export are combined.
def export_column(headers, rows, column_name, filepath):
    stats = get_column_stats(headers, rows, column_name)
    export_rows = [
        {"stat": "count",   "value": stats["count"]},
        {"stat": "min",     "value": _fmt_num(stats["min"])},
        {"stat": "max",     "value": _fmt_num(stats["max"])},
        {"stat": "average", "value": _fmt_num(stats["avg"])},
    ]
    _write_export(filepath, export_rows, ["stat", "value"])


# Saves the --missing data to a CSV file with two columns: "column" and "missing".
# One row per column showing how many blank cells it has. Used when --missing and --export are combined.
def export_missing(headers, rows, filepath):
    counts = get_missing_counts(headers, rows)
    export_rows = [{"column": col, "missing": n} for col, n in counts.items()]
    _write_export(filepath, export_rows, ["column", "missing"])


# Handles the --summary flag. Prints a Rich panel showing row and column counts,
# followed by a table listing each column name and its inferred type, color-coded
# by type (cyan = integer, yellow = float, white = string).
def cmd_summary(headers, rows, _console=None):
    c = _console or console
    info = get_summary(headers, rows)

    c.print(Panel(
        f"[green]{info['row_count']}[/green] rows  ·  "
        f"[green]{len(info['columns'])}[/green] columns",
        title="[bold blue]Summary[/bold blue]",
        border_style="blue",
    ))

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Column", style="white", min_width=20)
    table.add_column("Type", min_width=10)

    for col in info["columns"]:
        col_type = info["types"][col]
        color = _TYPE_COLORS.get(col_type, "white")
        table.add_row(col, f"[{color}]{col_type}[/{color}]")

    c.print(table)


# Handles the --column flag. Prints a Rich panel showing count, min, max, and average
# for the requested column, with the numeric values highlighted in bold green.
def cmd_column(headers, rows, column_name, _console=None):
    c = _console or console
    stats = get_column_stats(headers, rows, column_name)

    content = (
        f"[dim]Count[/dim]    {stats['count']} numeric values\n\n"
        f"[dim]Min[/dim]      [bold green]{_fmt_num(stats['min'])}[/bold green]\n"
        f"[dim]Max[/dim]      [bold green]{_fmt_num(stats['max'])}[/bold green]\n"
        f"[dim]Average[/dim]  [bold green]{_fmt_num(stats['avg'])}[/bold green]"
    )

    c.print(Panel(
        content,
        title=f"[bold blue]Column: {column_name}[/bold blue]",
        border_style="blue",
    ))


# Handles the --missing flag. Prints a Rich table showing how many blank cells
# each column has — red if any are missing, green if none. Shows a colored
# total missing count at the bottom.
def cmd_missing(headers, rows, _console=None):
    c = _console or console
    counts = get_missing_counts(headers, rows)
    total_missing = sum(counts.values())

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Column", style="white", min_width=20)
    table.add_column("Missing", justify="right", min_width=8)

    for col, n in counts.items():
        val = f"[red]{n}[/red]" if n > 0 else f"[green]{n}[/green]"
        table.add_row(col, val)

    c.print(table)

    total_color = "red" if total_missing > 0 else "green"
    c.print(f"\nTotal missing values: [{total_color}]{total_missing}[/{total_color}]")


# Entry point for the CLI. Sets up the four flags (--summary, --column, --missing, --export),
# reads the CSV file once, then calls whichever display and export functions match
# the flags the user passed. Prints help and exits cleanly if no flags are given.
def main():
    parser = argparse.ArgumentParser(
        prog="analyzer",
        description="Analyze CSV files from the command line.",
    )
    parser.add_argument("file", help="Path to the CSV file")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show row count, column names, and inferred data types",
    )
    parser.add_argument(
        "--column",
        metavar="COLUMN",
        help="Show min, max, and average for a numeric column",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        help="Show count of missing values per column",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Save output data to a CSV file (use with one data flag)",
    )

    args = parser.parse_args()

    no_data_flag = not args.summary and args.column is None and not args.missing
    if no_data_flag and args.export:
        _exit_error(
            "--export requires a data flag.\n"
            "Use it with --summary, --column COLUMN, or --missing."
        )
    if no_data_flag:
        parser.print_help()
        sys.exit(0)

    headers, rows = load_csv(args.file)

    if args.summary:
        cmd_summary(headers, rows)

    if args.column is not None:
        cmd_column(headers, rows, args.column)

    if args.missing:
        cmd_missing(headers, rows)

    if args.export:
        active = sum([args.summary, args.column is not None, args.missing])
        if active > 1:
            _exit_error(
                "--export requires exactly one data flag "
                "(--summary, --column, or --missing)."
            )
        if args.summary:
            export_summary(headers, rows, args.export)
        elif args.column is not None:
            export_column(headers, rows, args.column, args.export)
        elif args.missing:
            export_missing(headers, rows, args.export)
        console.print(f"\n[bold green]✓ Exported to {args.export}[/bold green]")


if __name__ == "__main__":
    main()
