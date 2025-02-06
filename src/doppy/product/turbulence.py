# type: ignore
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import polars as pl
import scipy
from scipy.interpolate import RegularGridInterpolator

from doppy.product.model import ModelWind
from doppy.product.noise import detect_noise
from doppy.product.stare import Stare
from doppy.product.turbulence_plots import *
from doppy.product.utils import VarResult
from doppy.product.wind import Wind


@dataclass
class HorizontalWind:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64]  # Height in meters from reference
    V: npt.NDArray[np.float64]  # Horizontal wind speed in m/s


@dataclass
class VerticalWind:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64]  # Height in meters from reference
    w: npt.NDArray[np.float64]  # Vertical wind speed in m/s
    mask: npt.NDArray[np.bool_]  # mask[t,h] = True iff w[t,h] should be masked


@dataclass
class Options:
    period: float = 600  # period for computing the variance
    pulses_per_ray: float = 10_000
    pulse_repetition_rate: float = 15e3  # 1/s
    beam_divergence: float = 33e-6  # radians


@dataclass
class Turbulence:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64]
    turbulent_kinetic_energy_dissipation_rate: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]

    @classmethod
    def from_winds(
        cls, vert: VerticalWind, hori: HorizontalWind, options: Options | None = None
    ):
        if options is None:
            options = Options()
        V = _preprocess_horiontal_wind(vert, hori, options)
        ls_low = _length_scale_low(V, vert.height, options)
        res = _compute_variance(vert, options.period)
        sampling_time = _sampling_time_in_seconds(res)
        ls_up = V * sampling_time
        dissipation_rate = _compute_dissipation_rate(res.variance, ls_low, ls_up)
        plot_dr(vert, dissipation_rate)


def _sampling_time_in_seconds(r: VarResult) -> npt.NDArray[np.float64]:
    if not all(
        (
            t == np.dtype("datetime64[us]")
            for t in (r.period_start.dtype, r.period_stop.dtype)
        )
    ):
        raise ValueError("period times must be on datetime64[us]")
    td = r.period_stop - r.period_start
    td_in_seconds = td / np.timedelta64(1, "s")
    return np.array(td_in_seconds, dtype=np.float64)


def _compute_variance(vert: VerticalWind, period: float) -> VarResult:
    # NOTE: numerically unstable

    # To compute actual time window
    next_valid = _next_valid_from_mask(vert.mask)
    prev_valid = _prev_valid_from_mask(vert.mask)

    X = vert.w.copy()
    X[vert.mask] = 0
    X2 = X**2
    X_cumsum = X.cumsum(axis=0)
    X2_cumsum = X2.cumsum(axis=0)

    N_i = (~vert.mask).astype(int)
    N_cumsum = N_i.cumsum(axis=0)

    def N_func(i: int, j: int) -> npt.NDArray[np.float64]:
        return N_cumsum[j] - N_cumsum[i] + N_i[i]

    def S(i: int, j: int) -> npt.NDArray[np.float64]:
        return X_cumsum[j] - X_cumsum[i] + X[i]

    def S2(i: int, j: int) -> npt.NDArray[np.float64]:
        return X2_cumsum[j] - X2_cumsum[i] + X2[i]

    def var_ij(i: int, j: int) -> npt.NDArray[np.float64]:
        N = N_func(i, j)
        with np.errstate(invalid="ignore"):
            return (S2(i, j) - S(i, j) ** 2 / N) / N

    half_period = np.timedelta64(int(1e6 * period / 2), "us")
    period_start = np.full(vert.w.shape, np.datetime64("NaT", "us"))
    period_stop = np.full(vert.w.shape, np.datetime64("NaT", "us"))
    var = np.full(vert.w.shape, np.nan, dtype=np.float64)
    nsamples = np.zeros_like(vert.w, dtype=np.int64)
    i = 0
    j = 0
    n = len(vert.time)
    for k, t in enumerate(vert.time):
        while i + 1 < n and t - vert.time[i + 1] >= half_period:
            i += 1
        while j + 1 < n and vert.time[j] - t < half_period:
            j += 1
        i_valid = next_valid[i]
        i_inbound = (0 <= i_valid) & (i_valid < n)
        j_valid = prev_valid[j]
        j_inbound = (0 <= j_valid) & (j_valid < n)
        period_start[k][i_inbound] = vert.time[i_valid[i_inbound]]
        period_stop[k][j_inbound] = vert.time[j_valid[j_inbound]]
        var[k] = var_ij(i, j)
        nsamples[k] = N_func(i, j)
    return VarResult(
        variance=var,
        period_start=period_start,
        period_stop=period_stop,
        nsamples=nsamples,
    )


def _length_scale_low(
    V: npt.NDArray[np.float64], height: npt.NDArray[np.float64], opts: Options
) -> npt.NDArray[np.float64]:
    integration_time = opts.pulses_per_ray / opts.pulse_repetition_rate
    from_beam = 2 * height * np.sin(opts.beam_divergence / 2)
    from_wind = V * integration_time
    return np.array(from_wind + from_beam[np.newaxis, :], dtype=np.float64)


def _preprocess_horiontal_wind(
    vert: VerticalWind, hori: HorizontalWind, options: Options
):
    if np.isnan(hori.V).any():
        raise ValueError("horizontal wind speed cannot contains NaNs")
    trg_points = np.meshgrid(vert.time, vert.height, indexing="ij")
    src_points = (hori.time, hori.height)
    src_vals = hori.V

    interp_nearest = RegularGridInterpolator(
        src_points,
        src_vals,
        method="nearest",
        bounds_error=False,
        fill_value=None,
    )
    interp_linear = RegularGridInterpolator(
        src_points, src_vals, method="linear", bounds_error=False
    )
    V_nearest = interp_nearest(trg_points)
    V_linear = interp_linear(trg_points)
    V = V_linear
    V[np.isnan(V)] = V_nearest[np.isnan(V)]
    if np.isnan(V).any():
        raise ValueError("Unexpected NaNs")
    V_rmean = _rolling_mean_over_time(vert.time, V, options.period)
    return V_rmean


def _rolling_mean_over_time(
    time: npt.NDArray[np.datetime64], arr: npt.NDArray[np.float64], period: float
) -> npt.NDArray[np.float64]:
    if arr.ndim != 2:
        raise ValueError("number of dims on arr should be 2")
    if time.ndim != 1 or time.shape[0] != arr.shape[0]:
        raise ValueError("time and arr dimensions do not match")
    if time.dtype != np.dtype("datetime64[us]"):
        raise TypeError(f"Invalid time type: {time.dtype}")

    S = arr.cumsum(axis=0)

    def rolling_mean(i: int, j: int) -> npt.NDArray[np.flaat64]:
        return (S[j] - S[i] + arr[i]) / (j - i + 1)

    half_period = np.timedelta64(int(period * 0.5e6), "us")
    rol_mean = np.full(arr.shape, np.nan, dtype=np.float64)

    i = 0
    j = 0
    n = len(time)
    for k, t in enumerate(time):
        while i + 1 < n and t - time[i + 1] >= half_period:
            i += 1
        while j + 1 < n and time[j] - t < half_period:
            j += 1
        rol_mean[k] = rolling_mean(i, j)
    return rol_mean


@dataclass
class TurbulenceOld:
    @classmethod
    def from_stare_and_wind(
        cls, stare: Stare, wind: Wind, model_wind: ModelWind, title: str
    ) -> None:
        window = 10 * 60  # in seconds
        pulses_per_ray = 10_000
        pulse_repetition_rate = 15e3  # 1/s
        integration_time = pulses_per_ray / pulse_repetition_rate
        beam_divergence = 33e-6  # radians
        if np.abs(np.median(stare.elevation) - 90) > 5 or np.var(stare.elevation) > 1:
            raise ValueError("Unexpected elevation")
        el_med = np.median(stare.elevation)
        el_var = np.var(stare.elevation)
        print(f"el_med: {el_med}, el_var: {el_var}")

        stare.mask = detect_noise(stare)

        wspeed, mask = _interpolate_wind_speed(stare, wind)
        wspeed_model = _interpolate_wind_speed_from_model(stare, model_wind)
        wspeed[mask] = wspeed_model[mask]
        # wspeed = wspeed_model  # use only model wind
        wspeed = _average_wind_speed(stare.time, wspeed, window)

        var_res = _compute_variance_old(stare, window)
        var_raw = _compute_variance_raw_polars(stare, window)
        sampling_time = (var_res.window_stop - var_res.window_start).astype(
            np.float64
        ) * 1e-6
        length_scale_upper = wspeed * sampling_time
        sampling_time_raw = np.full(sampling_time.shape, window)
        length_scale_upper_raw = wspeed * sampling_time_raw
        length_scale_lower = _compute_length_scale_lower_old(
            wspeed, stare.radial_distance, integration_time, beam_divergence
        )

        dissipation_rate = _compute_dissipation_rate(
            var_res.variance, length_scale_lower, length_scale_upper
        )
        dissipation_rate_raw = _compute_dissipation_rate(
            var_raw, length_scale_lower, length_scale_upper_raw
        )

        sample_th = max(3, np.median(var_res.nsamples[var_res.nsamples > 2]) * 0.55)

        dissipation_rate[var_res.nsamples < sample_th] = np.nan
        # plot_dr_old(stare, dissipation_rate, title)
        # plot_dr_old(stare, dissipation_rate_raw, f"raw-{title}")


def _average_wind_speed(
    time: npt.NDArray[np.datetime64], wspeed: npt.NDArray[np.float64], window: float
) -> npt.NDArray[np.float64]:
    if time.shape[0] != wspeed.shape[0]:
        raise ValueError
    if time.dtype != np.dtype("datetime64[us]"):
        raise TypeError(f"Invalid type: {time.dtype}")
    if np.isnan(wspeed).any():
        raise ValueError

    ws_avg = np.full(wspeed.shape, np.nan, dtype=np.float64)
    X = wspeed
    S = wspeed.cumsum(axis=0)

    def mean_func(i, j):
        return (S[j] - S[i] + X[i]) / (j - i + 1)

    half_window = np.timedelta64(int(1e6 * window / 2), "us")

    i = 0
    j = 0
    n = len(time)
    for k, t in enumerate(time):
        while i + 1 < n and t - time[i + 1] >= half_window:
            i += 1
        while j + 1 < n and time[j] - t < half_window:
            j += 1
        ws_avg[k] = mean_func(i, j)

    return ws_avg


def _compute_dissipation_rate(
    variance: npt.NDArray[np.float64],
    length_scale_lower: npt.NDArray[np.float64],
    length_scale_upper: npt.NDArray[np.float64],
):
    """
    Parameters
    ----------
    variance, length_scale_lower, and length_scale_upper
        dimensions: (time,range)
    """
    kolmogorov_constant = 0.55
    with np.errstate(invalid="ignore"):
        dr = (
            2
            * np.pi
            * (2 / (3 * kolmogorov_constant)) ** (3 / 2)
            * variance ** (3 / 2)
            * (length_scale_upper ** (2 / 3) - length_scale_lower ** (2 / 3))
            ** (-3 / 2)
        )
    return dr


def _compute_length_scale_lower_old(
    horizontal_wind_speed: npt.NDArray[np.float64],
    height: npt.NDArray[np.float64],
    integration_time: float,
    beam_divergence: float,
) -> npt.NDArray[np.float64]:
    from_beam = 2 * height * np.sin(beam_divergence / 2)
    from_wind = horizontal_wind_speed * integration_time
    return np.array(from_wind + from_beam[np.newaxis, :], dtype=np.float64)


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


def _compute_variance_raw_polars(stare: Stare, window: float):
    df = pl.from_numpy(stare.radial_velocity)
    df = df.with_columns(pl.Series("dt", stare.time))
    df_var = df.with_columns(
        pl.exclude("dt").rolling_var_by(
            "dt",
            window_size=f"{window}s",
            closed="both",
            ddof=0,
        ),
    )
    var = df_var.select(pl.exclude("dt")).to_numpy()
    return var


def _compute_variance_old(stare: Stare, window: float) -> VarResult:
    # NOTE: numerically unstable

    # To compute actual time window
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
