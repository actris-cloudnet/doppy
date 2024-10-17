from typing import TypeVar

import numpy as np
from numpy.typing import NDArray

T = TypeVar("T")


def merge_all_equal(key: str, lst: list[T]) -> T:
    if len(set(lst)) != 1:
        raise ValueError(f"Cannot merge header key {key} values {lst}")
    return lst[0]


def merge_all_close(key: str, lst: list[NDArray[T]]) -> T:
    if len(lst) == 0:
        raise ValueError(f"Cannot merge empty list for key {key}")
    if any(arr.size == 0 for arr in lst):
        raise ValueError(f"Cannot merge key {key}, one or more arrays are empty.")
    arr = np.concatenate([arr.flatten() for arr in lst])
    if not np.allclose(arr, arr[0]):
        raise ValueError(f"Cannot merge key {key}, values are not close enough")
    return arr[0]
