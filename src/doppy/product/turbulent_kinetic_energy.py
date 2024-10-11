from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import polars as pl
import scipy

from doppy.product.stare import Stare
from doppy.product.wind import Wind


@dataclass
class TurbulentKineticEnergy:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64]
    dissipation_rate: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]

    @classmethod
    def from_stare_and_wind(
        cls,
        stare: Stare,
        wind: Wind,
        integration_time: float = 1,
        beam_divergence: float = 33e-6,
    ) -> TurbulentKineticEnergy:
        """
        Parameters
        ----------
        integration_time : float, seconds
            Time used for individual measurement
            (pulses per ray / pulse repetition rate)

        beam_divergence : float, radians
        """
        kolmogorov_constant = 0.55
        horizontal_wind_speed = _interpolate_wind_speed(stare, wind)
        length_scale_individual = _compute_length_scale_individual(
            horizontal_wind_speed,
            stare.radial_distance,
            integration_time,
            beam_divergence,
        )
        # var, sampling_time = _compute_variance(stare, time_period=int(5 * 60))
        var, sampling_time = _compute_variance2(
            stare.time, stare.radial_velocity, stare.mask, int(1800)
        )

        length_scale_sampling = horizontal_wind_speed * sampling_time
        with np.errstate(invalid="ignore"):
            dissipation_rate = (
                2
                * np.pi
                * (2 / (3 * kolmogorov_constant)) ** (3 / 2)
                * var ** (3 / 2)
                * (
                    length_scale_sampling ** (2 / 3)
                    - length_scale_individual ** (2 / 3)
                )
                ** (-3 / 2)
            )
        return cls(
            time=stare.time,
            height=stare.radial_distance,
            dissipation_rate=np.array(dissipation_rate, dtype=np.float64),
            mask=stare.mask | np.isnan(dissipation_rate),
        )


def _gen_data():
    from datetime import datetime, timedelta

    np.random.seed(42)
    n = 81299
    m = 333

    start_time = datetime(2023, 1, 1)
    end_time = datetime(2023, 1, 2)
    time_delta = (end_time - start_time).total_seconds()
    random_seconds = np.random.uniform(0, time_delta, n)
    time = np.sort(
        np.array(
            [start_time + timedelta(seconds=sec) for sec in random_seconds],
            dtype="datetime64[us]",
        )
    )

    lower_bound = 0
    upper_bound = 12000
    height = np.sort(np.random.uniform(lower_bound, upper_bound, m))

    vel = np.random.rand(n, m).astype("float64")
    mask = np.random.choice([True, False], size=(n, m), p=[0.1, 0.9])
    return time, height, vel, mask


def _compute_variance3():
    # Implement Welfords online algo
    pass


def _compute_variance2(t, vel, mask, time_period_):
    time_period = np.timedelta64(int(time_period_ * 1e6), "us")
    t_ = np.repeat(t[:, np.newaxis], vel.shape[1], axis=1)
    vel[mask] = np.nan
    t_[mask] = np.datetime64("nat")
    start = np.full_like(vel, np.nan, dtype="datetime64[us]")
    stop = np.full_like(vel, np.nan, dtype="datetime64[us]")
    var = np.full_like(vel, np.nan)

    j = 0
    for i in range(len(t)):
        while j + 1 < len(t) and t[j + 1] - t[i] <= time_period:
            j += 1
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            start[i] = np.nanmin(t_[i : j + 1, :], axis=0)
            stop[i] = np.nanmax(t_[i : j + 1, :], axis=0)
            var[i] = np.nanvar(vel[i : j + 1], axis=0)

    sampling_time = (stop - start) / np.timedelta64(1, "s")
    return var, sampling_time


def _compute_variance(
    stare: Stare,
    time_period: int = 1800,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Parameters
    ----------
    time_period : int, seconds

    Returns
    -------
    var: array, dims: (time, height)
    sampling_time: array, dims: (time, 1), seconds

    """
    time_period_str = f"{time_period}s"
    radial_velocity = stare.radial_velocity
    radial_velocity[stare.mask] = np.nan
    df = pl.from_numpy(radial_velocity)
    df = df.with_columns(pl.Series("dt", stare.time))
    df_var = df.with_columns(
        pl.exclude("dt").rolling_var_by(
            "dt",
            window_size=time_period_str,
            closed="both",
            ddof=0,
        ),
    )
    df_time = df.rolling("dt", period=time_period_str, closed="both").agg(
        [
            pl.col("dt").min().alias("min_time"),
            pl.col("dt").max().alias("max_time"),
        ],
    )
    df_time = df_time.with_columns(
        (pl.col("max_time") - pl.col("min_time")).alias("time_diff"),
    )
    var = df_var.select(pl.exclude("dt")).to_numpy()
    timedelta_us = df_time["time_diff"].to_numpy()
    sampling_time = timedelta_us / np.timedelta64(1, "s")  # in seconds
    return np.array(var, dtype=np.float64), np.array(
        sampling_time[:, np.newaxis],
        dtype=np.float64,
    )


def _compute_length_scale_individual(
    horizontal_wind_speed: npt.NDArray[np.float64],
    height: npt.NDArray[np.float64],
    integration_time: float,
    beam_divergence: float,
) -> npt.NDArray[np.float64]:
    from_beam = 2 * height * np.sin(beam_divergence / 2)
    from_wind = horizontal_wind_speed * integration_time
    return np.array(from_wind + from_beam[np.newaxis, :], dtype=np.float64)


def _interpolate_wind_speed(stare: Stare, wind: Wind) -> npt.NDArray[np.float64]:
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


def test():
    t, h, vel, mask = _gen_data()
    var, sampling_time = _compute_variance2(t, vel, mask, 8)


if __name__ == "__main__":
    test()
