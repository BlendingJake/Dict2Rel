import pandas as pd
import polars as pl
import pytest

from dict2rel import ToRowsRequiredError, UnravelOptions, dict2rel, rel2dict

from .data import DOCSTRING_EXAMPLE_1, EXAMPLE_SMALL


def test_basic():
    """Test basic JSON -> tables"""
    tables = dict2rel([EXAMPLE_SMALL], lambda x: x)
    assert len(tables) == 4

    assert "*" in tables
    assert len(tables["*"]) == 1
    assert tables["*"][0]["name.first"] == EXAMPLE_SMALL["name"]["first"]

    assert "*.name.suffixes" in tables
    assert "_value" in tables["*.name.suffixes"][0]


@pytest.mark.parametrize(
    "provider",
    [
        pd.DataFrame,
        pl.DataFrame
    ]
)
def test_basic_with_providers(provider):
    """Test basic JSON -> tables with various providers"""
    tables = dict2rel(EXAMPLE_SMALL, provider)

    assert all(isinstance(v, provider) for v in tables.values())

    primary = tables["*"]
    assert "name.first" in primary
    assert primary["name.first"].to_list() == [EXAMPLE_SMALL["name"]["first"]]


def test_docstring_example_1():
    """Verify that the docstring example produces the expected result."""
    tables = dict2rel(
        DOCSTRING_EXAMPLE_1,
        pd.DataFrame,
        UnravelOptions(marker="Expanded {len} results to {sheet}")
    )

    assert len(tables) == 3

    tables_and_size = [
        ("*", 1),
        ("*.config.modules", 2),
        ("*.config.modules.*.settings.security.algorithms", 3)
    ]
    for t, s in tables_and_size:
        assert t in tables
        assert len(tables[t]) == s


def test_rel2dict_basic():
    """A basic example ensuring rel2dict works with polars and data
    which didn't originate with dict2rel.
    """
    objs = rel2dict(
        {
            "*": pl.DataFrame([
                {
                    "_id": "0",
                    "name": "Acme Corp.",
                    "state": "AZ",
                    "board": "4 board members in *.board"
                },
                {
                    "_id": "1",
                    "name": "ZZZ Consulting",
                    "state": "NY",
                    "board": "2 board members in *.board"
                }
            ]),
            "*.board": pl.DataFrame([
                {
                    "_id": "0.board.0",
                    "name": "Wile E. Coyote"
                },
                {
                    "_id": "0.board.1",
                    "name": "Someone Else"
                },
                {
                    "_id": "1.board.0",
                    "name": "Leonhard Euler"
                },
                {
                    "_id": "1.board.1",
                    "name": "Carl Gauss"
                }
            ])
        },
        lambda t: t.rows(named=True)
    )

    assert len(objs) == 2

    assert "board" in objs[0]
    assert len(objs[0]["board"]) == 2
    assert objs[0]["board"][1]["name"] == "Someone Else"

    assert "board" in objs[1]
    assert len(objs[1]["board"]) == 2
    assert objs[1]["board"][0]["name"] == "Leonhard Euler"


def test_rel2dict_with_missing_to_rows():
    """Verify that an error is thrown when to_rows is missing
    and the table is not just a list.
    """
    with pytest.raises(ToRowsRequiredError):
        rel2dict({"*": pl.DataFrame([])})


def test_reraveling_data_with_markers():
    """Verify that original data can be reconstructed even
    when markers were placed.
    """
    tables = dict2rel(EXAMPLE_SMALL, lambda x: x, UnravelOptions(marker="Expanded {len} values"))
    assert rel2dict(tables) == [EXAMPLE_SMALL]


def test_to_tables_and_back_basic():
    """Test JSON -> tables -> JSON"""
    tables = dict2rel([EXAMPLE_SMALL], lambda x: x)
    og = rel2dict(tables)

    assert og == [EXAMPLE_SMALL]


@pytest.mark.parametrize(
    ("provider", "to_rows"),
    [
        (pd.DataFrame, lambda t: (row for _, row in t.iterrows())),
        (pl.DataFrame, lambda t: t.rows(named=True))
    ]
)
def test_to_tables_and_back_providers(provider, to_rows):
    """Test JSON -> provider tables -> JSON"""
    tables = dict2rel(EXAMPLE_SMALL, provider)
    og = rel2dict(tables, to_rows)
    assert og == [EXAMPLE_SMALL]


def test_with_unravel_options():
    """Test custom marker language"""
    fmt = "{field} had {len} values placed in {sheet}"
    tables = dict2rel(
        EXAMPLE_SMALL,
        lambda x: x,
        UnravelOptions(marker=fmt)
    )

    assert "*" in tables
    assert "*.phones" in tables

    primary = tables["*"]
    assert len(primary) == 1
    assert "phones" in primary[0]
    assert primary[0]["phones"] == fmt.format(field="phones", len=2, sheet="*.phones")
