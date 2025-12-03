import polars as pl
import pytest

from dict2rel import ToRowsRequiredError, inflate


def test_inflate_with_missing_to_rows():
    """Verify that an error is thrown when to_rows is missing
    and the table is not just a list.
    """
    with pytest.raises(ToRowsRequiredError):
        inflate(pl.DataFrame([]))


def test_inflate_with_polars():
    """Test inflation example using a Polars DataFrame as the source"""
    tbl = pl.DataFrame([
        {
            "name": "Bravo",
            "version.major": "1",
            "version.minor": "0",
            "version.patch": "12",
            "releases.0.date": "2025-02-12",
            "releases.0.version": "0.0.1",
            "releases.1.date": "2025-02-18",
            "releases.1.version": "0.1.0"
        }
    ])

    results = inflate(tbl, lambda sheet: sheet.rows(named=True))

    assert len(results) == 1
    assert "releases" in results[0]
    assert len(results[0]["releases"]) == 2
    assert "version" in results[0]
    assert results[0]["version"]["major"] == "1"
