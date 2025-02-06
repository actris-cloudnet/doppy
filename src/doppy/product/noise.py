# type: ignore
import random
import warnings

import devboard as devb
import matplotlib
import matplotlib.colors
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import scipy

from doppy.product.stare import Stare


def detect_noise(stare: Stare):
    warnings.simplefilter("ignore", RuntimeWarning)
    v = rolling_median_over_range(
        stare.radial_distance,
        stare.radial_velocity,
        stare.mask,
        window=150,  # meters
        stride=1,
        fill_gaps=True,
    )

    th = 2
    diff = np.abs(v - stare.radial_velocity)
    new_mask = (diff > th) | stare.mask
    new_mask = _remove_one_hot(new_mask)
    return new_mask


def _remove_one_hot(m: npt.NDArray[np.bool_]):
    if m.ndim != 2:
        raise ValueError
    if m.shape[1] < 3:
        return m
    x = ~m
    y = np.full(x.shape, np.False_)
    y[:, 0] = x[:, 0] & x[:, 1]
    y[:, 1:-1] = x[:, 1:-1] & (x[:, 2:] | x[:, :-2])
    y[:, -1] = x[:, -1] & x[:, -2]
    return ~y


def _plot_algo(stare, v, new_mask, th):
    print("plotting..")
    nr = 100
    fig, ax = plt.subplots(3 + nr)
    n = len(ax)
    opts = {"vmin": -4, "vmax": 4, "cmap": "coolwarm"}
    T = stare.time
    N = len(T)
    R = stare.radial_distance
    V = stare.radial_velocity
    ax[0].pcolormesh(T, R, stare.radial_velocity.T, **opts)
    v_oldm = V.copy()
    v_oldm[stare.mask] = np.nan
    ax[1].pcolormesh(T, R, v_oldm.T, **opts)

    v_m = V.copy()
    v_m[new_mask] = np.nan
    ax[2].pcolormesh(T, R, v_m.T, **opts)

    for i, k in enumerate(random.sample(range(n), k=nr)):
        m = ~stare.mask[k]
        nm = ~new_mask[k]

        ax[3 + i].plot(R[m], v[k][m], color="b")
        ax[3 + i].fill_between(R[m], v[k][m] - th, v[k][m] + th, color="b", alpha=0.1)

        ax[3 + i].scatter(R[m], stare.radial_velocity[k][m], color="k")
        ax[3 + i].scatter(R[nm], stare.radial_velocity[k][nm], color="r")
        atwin = ax[3 + i].twinx()
        atwin.set_yscale("log")
        atwin.scatter(R[m], stare.snr[k][m], color="green")

    locator = matplotlib.dates.AutoDateLocator()
    for a in ax[:2]:
        a.xaxis.set_major_locator(locator)
        a.xaxis.set_major_formatter(matplotlib.dates.ConciseDateFormatter(locator))
    fig.set_size_inches((20, 4 * n))
    fig.tight_layout()
    devb.add_fig(fig)
    plt.close("all")


def rolling_mean_over_time(
    time: npt.NDArray[np.datetime64],
    arr: npt.NDArray[np.float64],
    mask: npt.NDArray[np.bool_],
    window: float,
):
    """
    window
        time window in seconds
    """
    if time.dtype != np.dtype("datetime64[us]"):
        raise TypeError(f"Invalid type: {time.dtype}")
    if np.isnan(arr).any():
        raise ValueError

    X = arr.copy()
    X[mask] = 0
    N_i = (~mask).astype(int)
    N_cumsum = N_i.cumsum(axis=0)

    S = arr.cumsum(axis=0)

    def N_func(i: int, j: int) -> int:
        return N_cumsum[j] - N_cumsum[i] + N_i[i]

    def S_func(i: int, j: int) -> np.float64:
        return S[j] - S[i] + X[i]

    def mean_func(i: int, j: int) -> np.float64:
        n = N_func(i, j)
        with np.errstate(divide="ignore", invalid="ignore"):
            val = S_func(i, j) / n
        val[n == 0] = np.nan
        return val

    half_window = np.timedelta64(int(1e6 * window / 2), "us")
    i = 0
    j = 0
    n = len(time)
    mean = np.full(arr.shape, np.nan, dtype=np.float64)
    for k, t in enumerate(time):
        while i + 1 < n and t - time[i + 1] >= half_window:
            i += 1
        while j + 1 < n and time[j] - t < half_window:
            j += 1
        if i > k or j < k:
            raise ValueError
        mean[k] = mean_func(i, j)
    return mean


def rolling_mean_over_range(
    range_: npt.NDArray[np.float64],
    arr: npt.NDArray[np.float64],
    mask: npt.NDArray[np.bool_],
    window: float,
):
    """
    window
        range window in meters
    """
    X = arr.T.copy()
    X[mask.T] = 0

    N_i = (~mask.T).astype(int)
    N_cumsum = N_i.cumsum(axis=0)

    S = X.cumsum(axis=0)

    def N_func(i: int, j: int) -> int:
        return N_cumsum[j] - N_cumsum[i] + N_i[i]

    def S_func(i: int, j: int) -> np.float64:
        return S[j] - S[i] + X[i]

    def mean_func(i: int, j: int) -> np.float64:
        n = N_func(i, j)
        with np.errstate(divide="ignore", invalid="ignore"):
            val = S_func(i, j) / n
        val[n == 0] = np.nan
        return val

    half_window = window / 2

    i = 0
    j = 0
    n = len(range_)
    mean = np.full(X.shape, np.nan, dtype=np.float64)
    for k, r in enumerate(range_):
        while i + 1 < n and r - range_[i + 1] >= half_window:
            i += 1
        while j + 1 < n and range_[j] - r < half_window:
            j += 1
        if i > k or j < k:
            raise ValueError
        mean[k] = mean_func(i, j)
    return mean.T.copy()


def rolling_var_over_range(
    range_: npt.NDArray[np.float64],
    arr: npt.NDArray[np.float64],
    mask: npt.NDArray[np.bool_],
    window: float,
):
    """
    window
        range window in meters
    """
    # TODO: numerically unstable
    X = arr.T.copy()
    X[mask.T] = 0
    X2 = X**2
    X_cumsum = X.cumsum(axis=0)
    X2_cumsum = X2.cumsum(axis=0)
    N_i = (~mask.T).astype(int)
    N_cumsum = N_i.cumsum(axis=0)

    def N_func(i, j):
        return N_cumsum[j] - N_cumsum[i] + N_i[i]

    def S(i, j):
        return X_cumsum[j] - X_cumsum[i] + X[i]

    def S2(i, j):
        return X2_cumsum[j] - X2_cumsum[i] + X2[i]

    def var_func(i, j):
        n = N_func(i, j)
        with np.errstate(invalid="ignore"):
            val = (S2(i, j) - S(i, j) ** 2 / n) / n
        val[n == 0] = np.nan
        return val

    half_window = window / 2

    i = 0
    j = 0
    n = len(range_)
    var = np.full(X.shape, np.nan, dtype=np.float64)
    for k, r in enumerate(range_):
        while i + 1 < n and r - range_[i + 1] >= half_window:
            i += 1
        while j + 1 < n and range_[j] - r < half_window:
            j += 1
        if i > k or j < k:
            raise ValueError
        var[k] = var_func(i, j)
    return var.T.copy()


def rolling_median_over_range(
    range_: npt.NDArray[np.float64],
    arr: npt.NDArray[np.float64],
    mask: npt.NDArray[np.bool_],
    window: float,
    stride: int = 1,
    fill_gaps: bool = False,
):
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
        f = scipy.interpolate.interp1d(
            range_[ind], med[ind], axis=0, fill_value="extrapolate"
        )
        med_all = f(range_)
        return med_all.T.copy()
    return med.T.copy()


def _plot_mean(arr, mask, mean, var=None):
    fig, ax = plt.subplots(4)
    opts = {"aspect": "auto", "origin": "lower"}

    # Define specific options for ax[0] and ax[2]
    color_opts = {"cmap": "coolwarm", "vmin": -4, "vmax": 4}
    ax[0].imshow(arr.T, **opts, **color_opts)
    ax[1].imshow(mask.T, **opts)
    ax[2].imshow(mean.T, **opts, **color_opts)

    k = arr.shape[0] // 2
    n = 200
    ax[3].plot(arr[k : k + n].T, color="k", alpha=0.01)
    ax[3].plot(mean[k + n // 2], color="r", alpha=1)
    if var is not None:
        std = var ** (0.5)
        ax[3].plot(mean[k + n // 2] + 3 * std[k + n // 2], color="b", alpha=1)
        ax[3].plot(mean[k + n // 2] - 3 * std[k + n // 2], color="b", alpha=1)

    fig.set_size_inches((22, 16))
    devb.add_fig(fig)
    plt.close("all")


def _plot(stare: Stare):
    n = 9
    fig, ax = plt.subplots(n)

    snr = stare.snr
    v = stare.radial_velocity
    time = stare.time.astype(float) * 1e-6
    height = stare.radial_distance
    grad = np.gradient(v, time, height, axis=(0, 1))
    grad_m = np.sqrt(grad[0] ** 2 + grad[1] ** 2)
    grad_d = np.arctan2(grad[0], grad[1])

    grad2 = np.gradient(grad_m, time, height, axis=(0, 1))
    grad2_m = np.sqrt(grad2[0] ** 2 + grad2[1] ** 2)

    var_opts = (
        (snr, {"vmin": np.percentile(snr, 1), "vmax": np.percentile(snr, 99)}),
        (v, {"vmin": -1, "vmax": 1, "cmap": "coolwarm"}),
        (
            grad[0],
            {"vmin": np.percentile(grad[0], 50), "vmax": np.percentile(grad[0], 90)},
        ),
        (
            grad[1],
            {"vmin": np.percentile(grad[1], 50), "vmax": np.percentile(grad[1], 90)},
        ),
        (grad_m, {"vmin": np.percentile(grad_m, 1), "vmax": np.percentile(grad_m, 10)}),
        (grad_d, {}),
        (
            grad2_m,
            {"vmin": np.percentile(grad2_m, 50), "vmax": np.percentile(grad2_m, 90)},
        ),
    )
    i = -1
    # for i, (var, opts) in enumerate(var_opts):
    #    mesh = ax[i].pcolormesh(time, height, var.T, **opts)

    # mask
    mask = (grad_m > np.percentile(grad_m, 25)) | (snr < np.percentile(snr, 75))
    v_masked = v.copy()
    v_masked[mask] = np.nan
    ax[i + 1].pcolormesh(
        time, height, v_masked.T, **{"vmin": -1, "vmax": 1, "cmap": "coolwarm"}
    )

    x = snr.ravel() - snr.min() + 1
    y = grad2_m.ravel() - grad2_m.min() + 1
    ax[i + 2].hexbin(x, y, xscale="log", yscale="log", norm=matplotlib.colors.LogNorm())
    k = time.size // 2
    ax[i + 3].plot(v[k : k + 20].T)

    fig.set_size_inches((22, 4 * n))
    fig.tight_layout()
    devb.add_fig(fig)
    plt.close("all")
