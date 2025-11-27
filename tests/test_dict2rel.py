import pandas as pd
import polars as pl
import pytest

from dict2rel import dict2rel, rel2dict

EXAMPLE = {
    "name": {
        "first": "John",
        "last": "Smith",
        "suffixes": [
            "MD",
            "JD"
        ]
    },
    "phones": [
        {
            "country": "USA",
            "number": "1234567890",
        },
        {
            "country": "ESP",
            "number": "987654321"
        }
    ],
    "matrix": [
        [1, 2],
        [3, 4]
    ]
}


def test_basic():
    """Test basic JSON -> tables"""
    tables = dict2rel([EXAMPLE], lambda x: x)
    assert len(tables) == 4

    assert "*" in tables
    assert len(tables["*"]) == 1
    assert tables["*"][0]["name.first"] == EXAMPLE["name"]["first"]

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
    tables = dict2rel(EXAMPLE, provider)

    assert all(isinstance(v, provider) for v in tables.values())

    primary = tables["*"]
    assert "name.first" in primary
    assert primary["name.first"].to_list() == [EXAMPLE["name"]["first"]]


def test_to_tables_and_back_basic():
    """Test JSON -> tables -> JSON"""
    tables = dict2rel([EXAMPLE], lambda x: x)
    og = rel2dict(tables)

    assert og == [EXAMPLE]


@pytest.mark.parametrize(
    "provider,to_rows",
    [
        (pd.DataFrame, lambda t: (row for _, row in t.iterrows())),
        (pl.DataFrame, lambda t: t.rows(named=True))
    ]
)
def test_to_tables_and_back_providers(provider, to_rows):
    """Test JSON -> provider tables -> JSON"""
    tables = dict2rel(EXAMPLE, provider)
    og = rel2dict(tables, to_rows)
    assert og == [EXAMPLE]
