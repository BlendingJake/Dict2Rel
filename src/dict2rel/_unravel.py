from __future__ import annotations

from typing import Iterator, NamedTuple

from dict2rel._types import ID_SENTINEL, VALUE_SENTINEL, FieldPath, JsonObject, JsonValue, Row, UnravelOptions

PartialMarker = NamedTuple(
    "PartialMarker",
    (("field", str), ("len", int), ("path", FieldPath))
)


def _determine_sheet_name(parts: FieldPath) -> str:
    sheet_parts = [
        "*" if isinstance(part, int) else part
        for part in parts
    ]

    if len(sheet_parts) > 1 and sheet_parts[-1] == "*":
        sheet_parts = sheet_parts[:-1]

    return ".".join(sheet_parts)


def unravel(obj: list[JsonObject], options: UnravelOptions) -> Iterator[tuple[str, Row]]:
    for fp, true_obj in _unravel(obj, [], options):
        _id = ".".join(map(str, fp))
        true_obj[ID_SENTINEL] = _id
        sheet = _determine_sheet_name(fp)

        for k, v in tuple(true_obj.items()):
            if isinstance(v, PartialMarker):
                if not options.marker:
                    del true_obj[k]
                else:
                    true_obj[k] = options.marker.format(
                        field=v.field,
                        id=_id,
                        len=v.len,
                        sheet=_determine_sheet_name(v.path)
                    )

        yield sheet, true_obj


def _unravel(obj: JsonValue, path: FieldPath, options: UnravelOptions) -> Iterator[tuple[FieldPath, Row]]:
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _unravel(v, [*path, i], options)
    elif isinstance(obj, dict):
        new_obj: Row = {}
        for k, v in obj.items():
            if isinstance(v, list):
                new_path: FieldPath = [*path, k]
                yield from _unravel(v, new_path, options)
                new_obj[k] = PartialMarker(field=k, len=len(v), path=new_path)
            elif isinstance(v, dict):
                for fp, nested_obj in _unravel(v, [*path, k], options):
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
