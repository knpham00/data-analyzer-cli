import sys
import pytest
from io import StringIO
from pathlib import Path
from rich.console import Console as RichConsole

sys.path.insert(0, str(Path(__file__).parent.parent))
from analyzer import (
    load_csv,
    get_summary,
    get_column_stats,
    get_missing_counts,
    export_summary,
    export_column,
    export_missing,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_console():
    """Return a (console, buffer) pair that captures Rich output as plain text."""
    buf = StringIO()
    c = RichConsole(file=buf, highlight=False, no_color=True)
    return c, buf


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_csv(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("name,age,score\nAlice,30,95.5\nBob,25,82.0\nCarol,35,88.0\n")
    return f


@pytest.fixture
def missing_csv(tmp_path):
    f = tmp_path / "missing.csv"
    f.write_text("name,age,score\nAlice,,95.5\nBob,25,\nCarol,,\n")
    return f


@pytest.fixture
def mixed_csv(tmp_path):
    f = tmp_path / "mixed.csv"
    f.write_text("id,value,label\n1,10,foo\n2,20,bar\n3,30,baz\n")
    return f


@pytest.fixture
def integer_csv(tmp_path):
    f = tmp_path / "ints.csv"
    f.write_text("x,y\n1,4\n2,5\n3,6\n")
    return f


# ---------------------------------------------------------------------------
# load_csv tests
# ---------------------------------------------------------------------------

class TestLoadCsv:
    def test_loads_headers_and_rows(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        assert headers == ["name", "age", "score"]
        assert len(rows) == 3

    def test_file_not_found_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            load_csv(tmp_path / "nonexistent.csv")

    def test_non_csv_extension_exits(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("a,b\n1,2\n")
        with pytest.raises(SystemExit):
            load_csv(f)

    def test_empty_file_exits(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("")
        with pytest.raises(SystemExit):
            load_csv(f)


# ---------------------------------------------------------------------------
# get_summary tests
# ---------------------------------------------------------------------------

class TestGetSummary:
    def test_row_count(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        summary = get_summary(headers, rows)
        assert summary["row_count"] == 3

    def test_column_names(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        summary = get_summary(headers, rows)
        assert summary["columns"] == ["name", "age", "score"]

    def test_inferred_types_string_and_numeric(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        summary = get_summary(headers, rows)
        assert summary["types"]["name"] == "string"
        assert summary["types"]["age"] in ("integer", "float")
        assert summary["types"]["score"] == "float"

    def test_integer_type_detection(self, integer_csv):
        headers, rows = load_csv(integer_csv)
        summary = get_summary(headers, rows)
        assert summary["types"]["x"] == "integer"
        assert summary["types"]["y"] == "integer"

    def test_mixed_column_types(self, mixed_csv):
        headers, rows = load_csv(mixed_csv)
        summary = get_summary(headers, rows)
        assert summary["types"]["id"] == "integer"
        assert summary["types"]["label"] == "string"


# ---------------------------------------------------------------------------
# get_column_stats tests
# ---------------------------------------------------------------------------

class TestGetColumnStats:
    def test_correct_min_max_avg(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        stats = get_column_stats(headers, rows, "score")
        assert stats["min"] == 82.0
        assert stats["max"] == 95.5
        assert abs(stats["avg"] - (95.5 + 82.0 + 88.0) / 3) < 1e-9

    def test_count_excludes_missing(self, missing_csv):
        headers, rows = load_csv(missing_csv)
        # missing_csv has score: 95.5, <empty>, <empty> — only 1 numeric value
        stats = get_column_stats(headers, rows, "score")
        assert stats["count"] == 1

    def test_unknown_column_exits(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        with pytest.raises(SystemExit):
            get_column_stats(headers, rows, "nonexistent")

    def test_non_numeric_column_exits(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        with pytest.raises(SystemExit):
            get_column_stats(headers, rows, "name")

    def test_integer_column_stats(self, integer_csv):
        headers, rows = load_csv(integer_csv)
        stats = get_column_stats(headers, rows, "x")
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0
        assert stats["avg"] == 2.0

    def test_single_value_column(self, tmp_path):
        f = tmp_path / "single.csv"
        f.write_text("val\n42\n")
        headers, rows = load_csv(f)
        stats = get_column_stats(headers, rows, "val")
        assert stats["min"] == stats["max"] == stats["avg"] == 42.0


# ---------------------------------------------------------------------------
# get_missing_counts tests
# ---------------------------------------------------------------------------

class TestGetMissingCounts:
    def test_no_missing_values(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        counts = get_missing_counts(headers, rows)
        assert all(v == 0 for v in counts.values())

    def test_counts_missing_correctly(self, missing_csv):
        headers, rows = load_csv(missing_csv)
        counts = get_missing_counts(headers, rows)
        assert counts["name"] == 0
        assert counts["age"] == 2
        assert counts["score"] == 2

    def test_all_columns_present_in_result(self, simple_csv):
        headers, rows = load_csv(simple_csv)
        counts = get_missing_counts(headers, rows)
        assert set(counts.keys()) == {"name", "age", "score"}

    def test_all_missing_column(self, tmp_path):
        f = tmp_path / "blanks.csv"
        f.write_text("a,b\n,\n,\n")
        headers, rows = load_csv(f)
        counts = get_missing_counts(headers, rows)
        assert counts["a"] == 2
        assert counts["b"] == 2


# ---------------------------------------------------------------------------
# CLI integration tests — use an injected StringIO console to capture output
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def test_summary_output(self, simple_csv):
        from analyzer import cmd_summary
        c, buf = _make_console()
        headers, rows = load_csv(simple_csv)
        cmd_summary(headers, rows, _console=c)
        out = buf.getvalue()
        assert "3" in out        # row count
        assert "name" in out
        assert "score" in out

    def test_summary_shows_types(self, simple_csv):
        from analyzer import cmd_summary
        c, buf = _make_console()
        headers, rows = load_csv(simple_csv)
        cmd_summary(headers, rows, _console=c)
        out = buf.getvalue()
        assert "string" in out
        assert "float" in out

    def test_column_output(self, simple_csv):
        from analyzer import cmd_column
        c, buf = _make_console()
        headers, rows = load_csv(simple_csv)
        cmd_column(headers, rows, "score", _console=c)
        out = buf.getvalue()
        assert "Min" in out
        assert "Max" in out
        assert "Average" in out

    def test_column_shows_values(self, simple_csv):
        from analyzer import cmd_column
        c, buf = _make_console()
        headers, rows = load_csv(simple_csv)
        cmd_column(headers, rows, "score", _console=c)
        out = buf.getvalue()
        assert "82" in out    # min value
        assert "95.5" in out  # max value

    def test_missing_output(self, missing_csv):
        from analyzer import cmd_missing
        c, buf = _make_console()
        headers, rows = load_csv(missing_csv)
        cmd_missing(headers, rows, _console=c)
        out = buf.getvalue()
        assert "age" in out
        assert "Total missing values" in out

    def test_missing_shows_total(self, missing_csv):
        from analyzer import cmd_missing
        c, buf = _make_console()
        headers, rows = load_csv(missing_csv)
        cmd_missing(headers, rows, _console=c)
        out = buf.getvalue()
        # age=2 missing, score=2 missing → total 4
        assert "4" in out

    def test_no_flags_exits_cleanly(self, simple_csv):
        from unittest.mock import patch
        with patch("sys.argv", ["analyzer", str(simple_csv)]):
            with pytest.raises(SystemExit) as exc_info:
                from analyzer import main
                main()
            assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------

class TestExport:
    def test_export_summary_creates_file(self, simple_csv, tmp_path):
        out = tmp_path / "summary.csv"
        headers, rows = load_csv(simple_csv)
        export_summary(headers, rows, out)
        assert out.exists()

    def test_export_summary_correct_content(self, simple_csv, tmp_path):
        out = tmp_path / "summary.csv"
        headers, rows = load_csv(simple_csv)
        export_summary(headers, rows, out)
        lines = out.read_text().splitlines()
        assert lines[0] == "column,type"
        assert lines[1].startswith("name,")
        assert "string" in lines[1]
        assert len(lines) == 4  # header + 3 columns

    def test_export_missing_correct_content(self, missing_csv, tmp_path):
        out = tmp_path / "missing.csv"
        headers, rows = load_csv(missing_csv)
        export_missing(headers, rows, out)
        lines = out.read_text().splitlines()
        assert lines[0] == "column,missing"
        # age has 2 missing values
        age_line = next(line for line in lines if line.startswith("age,"))
        assert age_line == "age,2"

    def test_export_column_correct_stats(self, simple_csv, tmp_path):
        out = tmp_path / "stats.csv"
        headers, rows = load_csv(simple_csv)
        export_column(headers, rows, "score", out)
        content = out.read_text()
        assert "stat,value" in content
        assert "min" in content
        assert "max" in content
        assert "average" in content
        assert "82" in content   # min value

    def test_export_column_count_row(self, simple_csv, tmp_path):
        out = tmp_path / "stats.csv"
        headers, rows = load_csv(simple_csv)
        export_column(headers, rows, "score", out)
        lines = out.read_text().splitlines()
        count_line = next(line for line in lines if line.startswith("count,"))
        assert count_line == "count,3"

    def test_export_multiple_flags_exits(self, simple_csv):
        from unittest.mock import patch
        from analyzer import main
        with patch("sys.argv", [
            "analyzer", str(simple_csv), "--summary", "--missing", "--export", "out.csv"
        ]):
            with pytest.raises(SystemExit):
                main()
