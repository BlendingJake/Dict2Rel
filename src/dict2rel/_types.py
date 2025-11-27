from typing import Dict, List, Union

FieldPath = List[Union[int, str]]

JsonPrimitive = Union[int, float, str, bool, None]
JsonValue = Union[JsonPrimitive, List['JsonValue'], 'JsonObject']
JsonObject = Dict[str, JsonValue]
Row = Dict[str, JsonPrimitive]

ID_SENTINEL = "_id"
VALUE_SENTINEL = "_value"
