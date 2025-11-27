# SPDX-FileCopyrightText: 2025-present Jacob Morris <blendingjake@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable, TypeVar, overload

if TYPE_CHECKING:
    from dict2rel._types import JsonObject, Row

from dict2rel._errors import ToRowsRequiredError
from dict2rel._ravel import ravel
from dict2rel._unravel import unravel

__all__ = ["dict2rel", "rel2dict"]
P = TypeVar("P")


def dict2rel(obj: list[JsonObject] | JsonObject, provider: Callable[[list[Row]], P]) -> dict[str, P]:
    """Take a list of JSON objects and convert them to tables using the
    provider of your choice (like Polars, Pandas, etc.). Nested arrays of
    JSON objects will be broken apart into their own tables while nested objects
    will be flattened.

    >>> dict2rel([
    ...     {
    ...         "name": {
    ...             "first": "John",
    ...             "last": "Smith"
    ...         },
    ...         "phones": [
    ...             {
    ...                 "country": "USA",
    ...                 "number": "1234567890"
    ...             },
    ...             {
    ...                 "country": "ESP",
    ...                 "number": "987654321"
    ...             }
    ...         ]
    ...     }
    ... ], pd.DataFrame)
    {
        "*": pd.DataFrame([
            {
                "_id": "0",
                "name.first": "John",
                "name.last": "Smith"
            }
        ]),
        "*.phones": pd.DataFrame([
            {
                "_id": "0.phones.0",
                "country": "USA",
                "number": "1234567890"
            },
            {
                "_id": "0.phones.1",
                "country": "ESP",
                "number": "987654321"
            }
        ])
    }
    """
    objs = [obj] if isinstance(obj, dict) else obj
    rows: dict[str, list[Row]] = {}
    for sheet, data in unravel(objs):
        if sheet not in rows:
            rows[sheet] = []

        rows[sheet].append(data)

    return {
        sheet: provider(rs)
        for sheet, rs in rows.items()
    }


@overload
def rel2dict(tables: dict[str, list[Row]]) -> list[JsonObject]:
    pass


@overload
def rel2dict(tables: dict[str, P], to_rows: Callable[[P], Iterable[Row]]) -> list[JsonObject]:
    pass


def rel2dict(tables: dict[str, list[Row] | P], to_rows: Callable[[P], Iterable[Row]] | None=None) -> list[JsonObject]:
    if not to_rows and not all(isinstance(rows, list) for rows in tables.values()):
        raise ToRowsRequiredError

    true_to_rows = to_rows if to_rows else lambda x: x
    return ravel({
        sheet: true_to_rows(rows)
        for sheet, rows in tables.items()
    })
