import numpy as np
import numpy.typing as npt


def arr_to_rounded_set(arr: npt.NDArray[np.float64]) -> set[int]:
    return set(int(x) for x in np.round(arr))
