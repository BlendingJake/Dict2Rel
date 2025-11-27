from __future__ import annotations

from typing import Iterator

from dict2rel._types import ID_SENTINEL, VALUE_SENTINEL, FieldPath, JsonObject, JsonValue, Row


def unravel(obj: list[JsonObject]) -> Iterator[tuple[str, Row]]:
    for fp, true_obj in _unravel(obj, []):
        sheet_parts = [
            "*" if isinstance(part, int) else part
            for part in fp
        ]

        if len(sheet_parts) > 1 and sheet_parts[-1] == "*":
            sheet_parts = sheet_parts[:-1]

        true_obj[ID_SENTINEL] = ".".join(map(str, fp))

        yield ".".join(sheet_parts), true_obj


def _unravel(obj: JsonValue, path: FieldPath) -> Iterator[tuple[FieldPath, Row]]:
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _unravel(v, [*path, i])
    elif isinstance(obj, dict):
        new_obj: Row = {}
        for k, v in obj.items():
            if isinstance(v, list):
                yield from _unravel(v, [*path, k])
            elif isinstance(v, dict):
                for fp, nested_obj in _unravel(v, [*path, k]):
                    if all(isinstance(part, str) for part in fp[len(path)+1:]):
                        for kk, vv in nested_obj.items():
                            new_obj[".".join([
                                k,
                                *list(map(str, fp[len(path)+1:])),
                                kk
                            ])] = vv
                    else:
                        yield fp, nested_obj
            else:
                new_obj[k] = v

        yield path, new_obj
    else:
        yield path, {VALUE_SENTINEL: obj}
