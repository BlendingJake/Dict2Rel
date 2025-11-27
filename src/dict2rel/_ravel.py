from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from dict2rel._types import JsonObject, JsonValue, Row

from dict2rel._types import ID_SENTINEL, VALUE_SENTINEL


def _parse_int_and_pad_parent(val: str, parent: list[JsonValue]) -> int:
    """Parse a string which is an int and then pad the length
    of parent to ensure the int will be a valid index.
    """
    value = int(val)
    parent.extend(None for _ in range(max(0, value - len(parent) + 1)))
    return value


def ravel(tables: dict[str, Iterable[Row]]) -> list[JsonObject]:
    # First, we need to reconstruct any nested dicts on all rows.
    id_to_value: dict[tuple[str, ...], JsonValue] = {}
    for rows in tables.values():
        for row in rows:
            id_to_value[tuple(row[ID_SENTINEL].split("."))] = _rebuild_row(row)

    # Figure out what is the most nested id and work from there up,
    # reconstructing the original values.
    most_nested = sorted(id_to_value, reverse=True)
    for parts in most_nested:
        if len(parts) <= 1:
            continue

        # Find the longest prefix id which exists in the lookup
        longest = (parts[0], )  # this has to be there
        for i in range(len(parts)-1):
            if parts[:i] in id_to_value:
                longest = parts[:i]

        # Build the layers that are missing between the closest parent
        # we found in the index and what is specified by this _id.
        parent = id_to_value[longest]
        left = parts[len(longest):]
        for i in range(len(left)-1):
            # The type of the current part being added is based on the
            # next part. If the next part is a numeric value, then this
            # thing we're adding must be a list. If it is a list, then make
            # sure it is long enough to handle the index we're setting.

            cur = left[i]
            _next = left[i+1]
            next_type = list if _next.isdigit() else dict

            if cur.isdigit():
                value = _parse_int_and_pad_parent(cur, parent)
                if not isinstance(parent[value], next_type):
                    parent[value] = next_type()

                parent = parent[value]
            else:
                if cur not in parent:
                    parent[cur] = next_type()

                parent = parent[cur]

        # We've built the intervening levels, so we can go ahead and
        # assign the value of interest to what we've built.
        if left[-1].isdigit():
            value = _parse_int_and_pad_parent(left[-1], parent)
            parent[value] = id_to_value[parts]
        else:
            parent[parts[-1]] = id_to_value[parts]

        # We've added this thing to its parent, so we can remove it
        # from the index. The bonus of this is that anything left at the
        # end must be a root/original row.
        del id_to_value[parts]

    return list(id_to_value.values())


def _rebuild_row(row: Row) -> JsonValue:
    """Take a row and rebuild any nested dicts that are present, remove
    the _id field, and handle any value-only rows. Rebuilding rows involves
    taking "name.first" and changing it back into {"name": {"first": ...}}.
    """
    # _id has to be there, so this must be a "value" row
    if len(row) == 2 and VALUE_SENTINEL in row:
        return row[VALUE_SENTINEL]

    new_obj: JsonObject = {}
    for key, value in row.items():
        if "." in key:
            parts = key.split(".")
            pointer = new_obj

            # Build any missing levels
            for part in parts[:-1]:
                if part not in pointer:
                    pointer[part] = {}

                pointer = pointer[part]

            # Assign the value to that last part
            pointer[parts[-1]] = value
        elif key != ID_SENTINEL:
            new_obj[key] = value

    return new_obj
