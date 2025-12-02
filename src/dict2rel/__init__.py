# SPDX-FileCopyrightText: 2025-present Jacob Morris <blendingjake@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable, TypeVar, overload

if TYPE_CHECKING:
    from dict2rel._types import JsonObject, Row

from dict2rel.__about__ import __version__
from dict2rel._errors import ToRowsRequiredError
from dict2rel._ravel import inflate as _inflate
from dict2rel._ravel import ravel as _ravel
from dict2rel._types import UnravelOptions
from dict2rel._unravel import flattener as _flattener
from dict2rel._unravel import unravel as _unravel

__all__ = ["dict2rel", "flatten", "rel2dict", "UnravelOptions"]
P = TypeVar("P")


def dict2rel(obj: list[JsonObject] | JsonObject, provider: Callable[[list[Row]], P], options: UnravelOptions | None = None) -> dict[str, P]:
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
    for sheet, data in _unravel(objs, options or UnravelOptions()):
        if sheet not in rows:
            rows[sheet] = []

        rows[sheet].append(data)

    return {
        sheet: provider(rs)
        for sheet, rs in rows.items()
    }


def flatten(obj: list[JsonObject] | JsonObject, provider: Callable[[list[Row]], P]) -> P:
    """Take a list of objects, or a single dict, and flatten it into
    a single sheet. Unlike :func:`dict2rel`, nested lists are kept on
    the primary sheet and provided a unique key. :func:`inflate` can be
    used to reverse this process.

    >>> flatten([
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
    ... ], pl.DataFrame)
    pl.DataFrame([
        {
            "_id": "0",
            "name.first": "John",
            "name.last": "Smith",
            "phones.0.country": "USA",
            "phones.0.number": "1234567890",
            "phones.1.country": "ESP",
            "phones.1.number": "987654321"
        }
    ])
    """
    objs = [obj] if isinstance(obj, dict) else obj
    return provider(list(_flattener(objs)))


def inflate(table: P, to_rows: Callable[[P], Iterable[Row]] | None = None) -> list[JsonObject]:
    """Undo :func:`flatten` and take a sheet with nesting represented by
    field names and inflate it back to a dictionary with actual nesting.
    """
    if not to_rows and not isinstance(table, list):
        raise ToRowsRequiredError

    true_to_rows = to_rows if to_rows else lambda x: x
    rows: Iterable[Row] = true_to_rows(table)
    return _inflate(rows)


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
    return _ravel({
        sheet: true_to_rows(rows)
        for sheet, rows in tables.items()
    })
