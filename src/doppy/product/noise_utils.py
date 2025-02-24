import warnings

import numpy as np
import numpy.typing as npt
import scipy


def detect_wind_noise(
    w: npt.NDArray[np.float64],
    height: npt.NDArray[np.float64],
    mask: npt.NDArray[np.bool_],
    window: float = 150,
    stride: int = 1,
) -> npt.NDArray[np.bool_]:
    """
    Parameters
    ----------
    w
        vertical velocity, dims: (time,height)

    height
        dims: (height,)

    mask
        old mask that still contains noisy velocity data,
        mask[t,h] = True iff w[t,h] is noise

    window
        size of window used to compute rolling median in meters

    stride
        stride used to compute rolling median

    Returns
    -------
    improved noise mask such that new_mask[t,h] = True iff w[t,h] is noise
    """
    warnings.simplefilter("ignore", RuntimeWarning)
    v = _rolling_median_over_range(
        height,
        w,
        mask,
        window=window,  # meters
        stride=stride,
        fill_gaps=True,
    )

    th = 2
    diff = np.abs(v - w)
    new_mask = (diff > th) | mask
    new_mask = _remove_one_hot(new_mask)
    return np.array(new_mask, dtype=np.bool_)


def _remove_one_hot(m: npt.NDArray[np.bool_]) -> npt.NDArray[np.bool_]:
    if m.ndim != 2:
        raise ValueError
    if m.shape[1] < 3:
        return m
    x = ~m
    y = np.full(x.shape, np.False_)
    y[:, 0] = x[:, 0] & x[:, 1]
    y[:, 1:-1] = x[:, 1:-1] & (x[:, 2:] | x[:, :-2])
    y[:, -1] = x[:, -1] & x[:, -2]
    return np.array(~y, dtype=np.bool_)


def _rolling_median_over_range(
    range_: npt.NDArray[np.float64],
    arr: npt.NDArray[np.float64],
    mask: npt.NDArray[np.bool_],
    window: float,
    stride: int = 1,
    fill_gaps: bool = False,
) -> npt.NDArray[np.float64]:
    """
    window
        range window in meters
    """
    X = arr.T.copy()
    X[mask.T] = np.nan

    half_window = window / 2

    i = 0
    j = 0
    n = len(range_)
    med = np.full(X.shape, np.nan, dtype=np.float64)
    for k in range(0, n, stride):
        r = range_[k]
        while i + 1 < n and r - range_[i + 1] >= half_window:
            i += 1
        while j + 1 < n and range_[j] - r < half_window:
            j += 1
        if i > k or j < k:
            raise ValueError
        med[k] = np.nanmedian(X[i : j + 1], axis=0)

    if stride != 1 and fill_gaps:
        ind = list(range(0, n, stride))
        f_interp = scipy.interpolate.interp1d(
            range_[ind], med[ind], axis=0, fill_value="extrapolate"
        )
        med_all = f_interp(range_)
        return np.array(med_all.T.copy(), dtype=np.float64)
    return np.array(med.T.copy(), dtype=np.float64)
