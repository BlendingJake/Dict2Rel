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


@pytest.mark.parametrize("provider", [pd.DataFrame, pl.DataFrame])
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
        UnravelOptions(marker="Expanded {len} results to {sheet}"),
    )

    assert len(tables) == 3

    tables_and_size = [
        ("*", 1),
        ("*.config.modules", 2),
        ("*.config.modules.*.settings.security.algorithms", 3),
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
            "*": pl.DataFrame(
                [
                    {
                        "_id": "0",
                        "name": "Acme Corp.",
                        "state": "AZ",
                        "board": "4 board members in *.board",
                    },
                    {
                        "_id": "1",
                        "name": "ZZZ Consulting",
                        "state": "NY",
                        "board": "2 board members in *.board",
                    },
                ]
            ),
            "*.board": pl.DataFrame(
                [
                    {"_id": "0.board.0", "name": "Wile E. Coyote"},
                    {"_id": "0.board.1", "name": "Someone Else"},
                    {"_id": "1.board.0", "name": "Leonhard Euler"},
                    {"_id": "1.board.1", "name": "Carl Gauss"},
                ]
            ),
        }
    )

    assert len(objs) == 2

    assert "board" in objs[0]
    assert len(objs[0]["board"]) == 2
    assert objs[0]["board"][1]["name"] == "Someone Else"

    assert "board" in objs[1]
    assert len(objs[1]["board"]) == 2
    assert objs[1]["board"][0]["name"] == "Leonhard Euler"


def test_reraveling_data_with_forcibly_expanded_fields():
    """Verify that unraveled data with field paths set for objects to
    expand can be raveled by up. They won't be the exact same as the
    raveling won't know that it was a nested object that was expanded
    because of the UnravelOptions.
    """
    data = {
        "name": 1,
        "version": {"major": 1},
        "authors": [{"name": {"first": "John", "last": "Smith"}}],
    }

    tables = dict2rel(
        data,
        lambda x: x,
        UnravelOptions(fields_to_expand=["authors.name", "version"]),
    )
    raveled = rel2dict(tables)

    assert len(raveled) == 1

    assert "version" in raveled[0]
    assert isinstance(raveled[0]["version"], list)
    assert raveled[0]["version"][0]["major"] == 1

    assert "authors" in raveled[0]
    authors = raveled[0]["authors"]
    assert isinstance(authors, list)
    assert len(authors) == 1
    assert isinstance(authors[0], dict)
    assert "name" in authors[0]
    assert isinstance(authors[0]["name"], list)
    assert authors[0]["name"][0]["first"] == "John"


def test_reraveling_data_with_markers():
    """Verify that original data can be reconstructed even
    when markers were placed.
    """
    tables = dict2rel(
        EXAMPLE_SMALL,
        lambda x: x,
        UnravelOptions(marker="Expanded {len} values"),
    )
    assert rel2dict(tables) == [EXAMPLE_SMALL]


@pytest.mark.parametrize(
    ("provider", "to_rows"),
    [
        (pd.DataFrame, None),
        (pl.DataFrame, None),
        (lambda x: x, None),
        (lambda x: x, lambda x: x),
    ],
)
def test_to_row_options(provider, to_rows):
    """Verify all of the ways to_rows can be provided"""
    tables = dict2rel(EXAMPLE_SMALL, provider)
    og = rel2dict(tables, to_rows)

    assert og[0] == EXAMPLE_SMALL


def test_to_row_not_provider():
    """Verify that an error is thrown when to_rows is not provided
    and the table-type is not known/supported.
    """

    class MyTable(pd.DataFrame):
        pass

    tables = dict2rel(EXAMPLE_SMALL, MyTable)
    with pytest.raises(ToRowsRequiredError):
        rel2dict(tables)


def test_to_tables_and_back_basic():
    """Test JSON -> tables -> JSON"""
    tables = dict2rel([EXAMPLE_SMALL], lambda x: x)
    og = rel2dict(tables)

    assert og == [EXAMPLE_SMALL]


@pytest.mark.parametrize(
    "provider",
    [pd.DataFrame, pl.DataFrame],
)
def test_to_tables_and_back_providers(provider):
    """Test JSON -> provider tables -> JSON"""
    tables = dict2rel(EXAMPLE_SMALL, provider)
    og = rel2dict(tables)
    assert og == [EXAMPLE_SMALL]


def test_unravel_with_specified_fields_to_expand():
    """Verify that nested objects can be forced to separate
    sheets by specifying the path in the UnravelOptions.
    """
    data = {
        "name": 1,
        "version": {"major": 1},
        "authors": [{"name": {"first": "John", "last": "Smith"}}],
    }

    not_expanded = dict2rel(data, lambda x: x)
    assert len(not_expanded) == 2

    expanded = dict2rel(
        data,
        lambda x: x,
        UnravelOptions(fields_to_expand=["authors.name", "version"]),
    )
    assert len(expanded) == 4

    assert "*.version" in expanded
    assert "version" not in expanded["*"][0]

    assert "*.authors.*.name" in expanded
    assert "first" in expanded["*.authors.*.name"][0]


def test_with_unravel_marker():
    """Test custom marker language"""
    fmt = "{field} had {len} values placed in {sheet}"
    tables = dict2rel(EXAMPLE_SMALL, lambda x: x, UnravelOptions(marker=fmt))

    assert "*" in tables
    assert "*.phones" in tables

    primary = tables["*"]
    assert len(primary) == 1
    assert "phones" in primary[0]
    assert primary[0]["phones"] == fmt.format(field="phones", len=2, sheet="*.phones")
