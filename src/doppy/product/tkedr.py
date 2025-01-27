from __future__ import annotations

from dataclasses import dataclass

import devboard as devb
import matplotlib.colors
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import scipy

from doppy.product.model import ModelWind
from doppy.product.stare import Stare
from doppy.product.wind import Wind


@dataclass
class Tkedr:
    @classmethod
    def from_stare_and_wind(
        cls, stare: Stare, wind: Wind, model_wind: ModelWind, title: str
    ) -> None:
        window = 30 * 60  # in seconds
        beam_divergence = 33e-6
        kolmogorov_constant = 0.55
        pulses_per_ray = 10_000
        pulse_repetition_rate = 15e3  # 1/s
        integration_time = pulses_per_ray / pulse_repetition_rate
        beam_divergence = 33e-6  # radians

        wspeed, mask = _interpolate_wind_speed(stare, wind)
        wspeed_model = _interpolate_wind_speed_from_model(stare, model_wind)
        wspeed[mask] = wspeed_model[mask]

        var_res = _compute_variance(stare, window)
        sampling_time = (var_res.window_stop - var_res.window_start).astype(
            np.float64
        ) * 1e-6
        length_scale_upper = wspeed * sampling_time
        length_scale_lower = _compute_length_scale_lower(
            wspeed, stare.radial_distance, integration_time, beam_divergence
        )
        var = var_res.variance

        with np.errstate(invalid="ignore"):
            dissipation_rate = (
                2
                * np.pi
                * (2 / (3 * kolmogorov_constant)) ** (3 / 2)
                * var ** (3 / 2)
                * (length_scale_upper ** (2 / 3) - length_scale_lower ** (2 / 3))
                ** (-3 / 2)
            )
        sample_th = max(3, np.median(var_res.nsamples[var_res.nsamples > 2]) * 4 / 5)

        dissipation_rate[var_res.nsamples < sample_th] = np.nan
        _plot_dr(stare, dissipation_rate, title)


def _plot_var_res(r: VarResult, stare: Stare):
    fig, ax = plt.subplots()

    window = (r.window_stop - r.window_start).astype(float) * 1e-6 / 60
    mesh = ax.pcolormesh(
        stare.time,
        stare.radial_distance,
        window.T,
        norm=matplotlib.colors.LogNorm(vmin=1 / 60, vmax=window.max()),
    )
    fig.colorbar(mesh, ax=ax)

    devb.add_fig(fig)


def _plot_dr(stare, dr, title):
    fig, ax = plt.subplots(2)
    range_mask = stare.radial_distance < 4000

    mesh = ax[0].pcolormesh(
        stare.time,
        stare.radial_distance[range_mask],
        dr[:, range_mask].T,
        norm=matplotlib.colors.LogNorm(vmin=1e-6, vmax=5 * 1e-3),
        cmap="plasma",
    )
    fig.colorbar(
        mesh, ax=ax[0], orientation="horizontal", shrink=0.5, pad=0.1
    ).outline.set_visible(False)  # type: ignore

    mesh = ax[1].pcolormesh(
        stare.time,
        stare.radial_distance[range_mask],
        stare.radial_velocity[:, range_mask].T,
        cmap="coolwarm",
        vmin=-4,
        vmax=4,
    )

    fig.colorbar(
        mesh, ax=ax[1], orientation="horizontal", shrink=0.5, pad=0.1
    ).outline.set_visible(False)  # type: ignore

    locator = matplotlib.dates.AutoDateLocator()

    ax[0].set_title(title)
    for i in range(len(ax)):
        ax[i].xaxis.set_major_locator(locator)
        ax[i].xaxis.set_major_formatter(matplotlib.dates.ConciseDateFormatter(locator))
        ax[i].spines["left"].set_visible(False)
        ax[i].spines["top"].set_visible(False)
        ax[i].spines["right"].set_visible(False)
        ax[i].spines["bottom"].set_visible(False)

    fig.set_size_inches(22, 16)
    devb.add_fig(fig)


def _compute_length_scale_lower(
    horizontal_wind_speed: npt.NDArray[np.float64],
    height: npt.NDArray[np.float64],
    integration_time: float,
    beam_divergence: float,
) -> npt.NDArray[np.float64]:
    from_beam = 2 * height * np.sin(beam_divergence / 2)
    from_wind = horizontal_wind_speed * integration_time
    return np.array(from_wind + from_beam[np.newaxis, :], dtype=np.float64)


def _plot_interpolaterd_wind(stare, wind, iwind):
    fig, ax = plt.subplots(3)
    wspeed = np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2)
    ax[0].pcolormesh(wind.time, wind.height, wspeed.T)
    ax[1].pcolormesh(wind.time, wind.height, wind.mask.T)

    ax[2].pcolormesh(stare.time, stare.radial_distance, iwind.T)

    devb.add_fig(fig)


@dataclass
class VarResult:
    variance: npt.NDArray[np.float64]
    window_start: npt.NDArray[np.datetime64]
    window_stop: npt.NDArray[np.datetime64]
    nsamples: npt.NDArray[np.int64]


def _next_valid_from_mask(mask):
    """
    mask[t,v] (time,value)

    returns N[t,v] = i where i = min { j | j >= t and mask[j,v] == False}
    if the set is non empty and N[t,v] = len(mask) otherwise
    """
    n = len(mask)
    N = np.full(mask.shape, n)
    if mask.size == 0:
        return N
    N[-1][~mask[-1]] = n - 1

    for t in reversed(range(n - 1)):
        N[t][~mask[t]] = t
        N[t][mask[t]] = N[t + 1][mask[t]]
    return N


def _prev_valid_from_mask(mask):
    """
    mask[t,v] (time,value)

    returns N[t,v] = i where i = max { j | j <= t and mask[j,v] == False}
    if the set is non empty and N[t,v] = -1 otherwise
    """
    n = len(mask)
    N = np.full(mask.shape, -1)
    if mask.size == 0:
        return N
    N[0][~mask[0]] = 0
    for t in range(1, n):
        N[t][~mask[t]] = t
        N[t][mask[t]] = N[t - 1][mask[t]]
    return N


def _plot_next_valid(N):
    fig, ax = plt.subplots()
    ax.plot(N)
    devb.add_fig(fig)


def _compute_variance(stare: Stare, window: float) -> VarResult:
    # NOTE: numerically unstable

    next_valid = _next_valid_from_mask(stare.mask)
    prev_valid = _prev_valid_from_mask(stare.mask)

    X = stare.radial_velocity.copy()
    X[stare.mask] = 0
    X2 = X**2
    X_cumsum = X.cumsum(axis=0)
    X2_cumsum = X2.cumsum(axis=0)

    N_i = (~stare.mask).astype(int)
    N_cumsum = N_i.cumsum(axis=0)

    def N_func(i, j):
        return N_cumsum[j] - N_cumsum[i] + N_i[i]

    def S(i, j):
        return X_cumsum[j] - X_cumsum[i] + X[i]

    def S2(i, j):
        return X2_cumsum[j] - X2_cumsum[i] + X2[i]

    def var_ij(i, j):
        N = N_func(i, j)
        with np.errstate(invalid="ignore"):
            return (S2(i, j) - S(i, j) ** 2 / N) / N

    half_window = np.timedelta64(int(1e6 * window / 2), "us")
    window_start = np.full(stare.radial_velocity.shape, np.datetime64("NaT", "us"))
    window_stop = np.full(stare.radial_velocity.shape, np.datetime64("NaT", "us"))
    var = np.full(stare.radial_velocity.shape, np.nan, dtype=np.float64)
    nsamples = np.zeros_like(stare.radial_velocity, dtype=np.int64)
    i = 0
    j = 0
    n = len(stare.time)
    for k, t in enumerate(stare.time):
        while i + 1 < n and t - stare.time[i + 1] >= half_window:
            i += 1
        while j + 1 < n and stare.time[j] - t < half_window:
            j += 1
        i_valid = next_valid[i]
        i_inbound = (0 <= i_valid) & (i_valid < n)
        j_valid = prev_valid[j]
        j_inbound = (0 <= j_valid) & (j_valid < n)
        window_start[k][i_inbound] = stare.time[i_valid[i_inbound]]
        window_stop[k][j_inbound] = stare.time[j_valid[j_inbound]]
        var[k] = var_ij(i, j)
        nsamples[k] = N_func(i, j)
    return VarResult(
        variance=var,
        window_start=window_start,
        window_stop=window_stop,
        nsamples=nsamples,
    )


def plot_var(var, stare):
    fig, ax = plt.subplots()

    ax.pcolormesh(stare.time, stare.radial_distance, var.T)
    devb.add_fig(fig)


def _interpolate_wind_speed(
    stare: Stare, wind: Wind
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.bool_]]:
    """
    Interpolates horizontal wind speed from wind (time, height) dimensions
    into stare (time, range) dimensions.
    Points that are not in wind dimension bounds are extrapolated using nearest points
    """
    horizontal_wind_speed = np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2)
    interpolator_nearest = scipy.interpolate.RegularGridInterpolator(
        (wind.time, wind.height),
        horizontal_wind_speed,
        method="nearest",
        bounds_error=False,
        fill_value=None,
    )
    interpolator_linear = scipy.interpolate.RegularGridInterpolator(
        (wind.time, wind.height),
        horizontal_wind_speed,
        bounds_error=False,
        method="linear",
    )
    time, height = np.meshgrid(stare.time, stare.radial_distance, indexing="ij")
    interpolated_wind_speed_linear = interpolator_linear((time, height))
    interpolated_wind_speed_nearest = interpolator_nearest((time, height))
    isnan = np.isnan(interpolated_wind_speed_linear)
    interpolated_wind_speed_linear[isnan] = interpolated_wind_speed_nearest[isnan]

    # Mask
    mask = wind.mask.astype(np.float64)
    interpolator_linear_for_mask = scipy.interpolate.RegularGridInterpolator(
        (wind.time, wind.height),
        mask,
        bounds_error=False,
        method="linear",
    )
    interpolated_mask_float = interpolator_linear_for_mask((time, height))

    interpolated_mask_bool = np.full(interpolated_mask_float.shape, False)
    interpolated_mask_bool[
        np.isnan(interpolated_mask_float)
        | (interpolated_mask_float > np.finfo(np.float64).eps)
    ] = True

    return np.array(interpolated_wind_speed_linear, dtype=np.float64), np.array(
        interpolated_mask_bool, dtype=np.bool_
    )


def _interpolate_wind_speed_from_model(
    stare: Stare, wind: ModelWind
) -> npt.NDArray[np.float64]:
    """
    Interpolates horizontal wind speed from wind (time, height) dimensions
    into stare (time, range) dimensions.
    Points that are not in wind dimension bounds are extrapolated using nearest points
    """
    horizontal_wind_speed = np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2)
    interpolator_nearest = scipy.interpolate.RegularGridInterpolator(
        (wind.time, wind.height),
        horizontal_wind_speed,
        method="nearest",
        bounds_error=False,
        fill_value=None,
    )
    interpolator_linear = scipy.interpolate.RegularGridInterpolator(
        (wind.time, wind.height),
        horizontal_wind_speed,
        bounds_error=False,
        method="linear",
    )
    time, height = np.meshgrid(stare.time, stare.radial_distance, indexing="ij")
    interpolated_wind_speed_linear = interpolator_linear((time, height))
    interpolated_wind_speed_nearest = interpolator_nearest((time, height))
    isnan = np.isnan(interpolated_wind_speed_linear)
    interpolated_wind_speed_linear[isnan] = interpolated_wind_speed_nearest[isnan]

    return np.array(interpolated_wind_speed_linear, dtype=np.float64)


def _plot_interpolated_mask(stare, wind, mask):
    fig, ax = plt.subplots()
    pmesh = ax.pcolormesh(stare.time, stare.radial_distance, mask.T)
    ax.set_title("mask")

    devb.add_fig(fig)
