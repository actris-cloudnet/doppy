from typing import TypeVar

T = TypeVar("T")


def merge_all_equal(key: str, lst: list[T]) -> T:
    if len(set(lst)) != 1:
        raise ValueError(f"Cannot merge header key {key} values {lst}")
    return lst[0]
