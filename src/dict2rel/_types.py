from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Union

FieldPath = List[Union[int, str]]

JsonPrimitive = Union[int, float, str, bool, None]
JsonValue = Union[JsonPrimitive, List['JsonValue'], 'JsonObject']
JsonObject = Dict[str, JsonValue]
Row = Dict[str, JsonPrimitive]

ID_SENTINEL = "_id"
VALUE_SENTINEL = "_value"


@dataclass
class UnravelOptions:
    """Options for configuring how an object is unraveled and
    expanded into one or more tables. Used by :func:`dict2rel.dict2rel`.
    """

    marker: str | None = None
    """The value, if any, which will be placed in a column when
    the value was a list and therefore got expanded to its own table.
    By default, the column is not included.

    String interpolation is supported and the provided values are:

    * ``field: str`` - the name of the field being expanded
    * ``id: str`` - the ``_id`` of the current row
    * ``len: int`` - the length of the nested list
    * ``sheet: str`` - the name of the sheet where the nested values
      were placed

    An example marker value would be: ``"{len} values placed in {sheet}"``.
    """
