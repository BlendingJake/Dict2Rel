from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Dict, Iterable, List, Union

FieldPath = List[Union[int, str]]

JsonPrimitive = Union[int, float, str, bool, None]
JsonValue = Union[JsonPrimitive, List["JsonValue"], "JsonObject"]
JsonObject = Dict[str, JsonValue]
Row = Dict[str, JsonPrimitive]

ID_SENTINEL = "_id"
VALUE_SENTINEL = "_value"


@dataclass
class UnravelOptions:
    """Options for configuring how an object is unraveled and
    expanded into one or more tables. Used by :func:`dict2rel.dict2rel`.
    """

    fields_to_expand: Iterable[str] | None = None
    """Field paths which point to nested objects which should be expanded
    to their own tables instead of being flattened inline. Essentially,
    this will treat the nested objects as if they were nested lists.

    The field paths should ignore any nested arrays and mirror field paths
    seen in query languages like ElasticSearch's DSL.

    >>> data = [
    ...     {
    ...         "addresses": {
    ...
    ...         }
    ...     }
    ... ]
    >>> UnravelOptions(
    ...     fields_to_expand=["addresses"]  # not *.addresses
    ... )

    .. note::
        Fields which are expanded to separate tables can be reconstructed with
        :func:`~dict2rel.rel2dict`, but will be reconstructed as lists of a single
        object instead of just as an object.

    .. versionadded:: 0.0.2
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

    @cached_property
    def fields_to_expand_set(self) -> set[str]:
        if self.fields_to_expand:
            return set(self.fields_to_expand)

        return set()
