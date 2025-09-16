from __future__ import annotations

import functools
from collections import Counter
from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt
from scipy.ndimage import generic_filter

import doppy
from doppy.product.utils import arr_to_rounded_set


@dataclass
class Options:
    azimuth_offset_deg: float | None


@dataclass
class Wind:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64]
    zonal_wind: npt.NDArray[np.float64]
    meridional_wind: npt.NDArray[np.float64]
    vertical_wind: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]
    system_id: str
    options: Options | None

    @property
    def mask_zonal_wind(self) -> npt.NDArray[np.bool_]:
        return np.isnan(self.zonal_wind)

    @property
    def mask_meridional_wind(self) -> npt.NDArray[np.bool_]:
        return np.isnan(self.meridional_wind)

    @property
    def mask_vertical_wind(self) -> npt.NDArray[np.bool_]:
        return np.isnan(self.vertical_wind)

    @functools.cached_property
    def horizontal_wind_speed(self) -> npt.NDArray[np.float64]:
        return np.sqrt(self.zonal_wind**2 + self.meridional_wind**2)

    @functools.cached_property
    def horizontal_wind_direction(self) -> npt.NDArray[np.float64]:
        direction = np.arctan2(self.zonal_wind, self.meridional_wind)
        direction[direction < 0] += 2 * np.pi
        return np.array(np.degrees(direction), dtype=np.float64)

    @classmethod
    def from_halo_data(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
        options: Options | None = None,
    ) -> Wind:
        raws = doppy.raw.HaloHpl.from_srcs(data)

        if len(raws) == 0:
            raise doppy.exceptions.NoDataError("HaloHpl data missing")

        raw = (
            doppy.raw.HaloHpl.merge(_select_raws_for_wind(raws))
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
            .nans_removed()
        )
        if len(raw.time) == 0:
            raise doppy.exceptions.NoDataError("No suitable data for the wind product")

        if options and options.azimuth_offset_deg:
            raw.azimuth += options.azimuth_offset_deg

        groups = _group_scans_by_azimuth_rotation(raw)
        time_list = []
        elevation_list = []
        wind_list = []
        rmse_list = []

        for group_index in set(groups):
            pick = group_index == groups
            if pick.sum() < 4:
                continue
            time_, elevation_, wind_, rmse_ = _compute_wind(raw[pick])
            time_list.append(time_)
            elevation_list.append(elevation_)
            wind_list.append(wind_[np.newaxis, :, :])
            rmse_list.append(rmse_[np.newaxis, :])
        time = np.array(time_list)
        if len(time) == 0:
            raise doppy.exceptions.NoDataError(
                "Probably something wrong with scan grouping"
            )
        elevation = np.array(elevation_list)
        wind = np.concatenate(wind_list)
        rmse = np.concatenate(rmse_list)
        if not np.allclose(elevation, elevation[0]):
            raise ValueError("Elevation is expected to stay same")
        height = raw.radial_distance * np.sin(np.deg2rad(elevation[0]))
        mask = _compute_mask(wind, rmse)
        return Wind(
            time=time,
            height=height,
            zonal_wind=wind[:, :, 0],
            meridional_wind=wind[:, :, 1],
            vertical_wind=wind[:, :, 2],
            mask=mask,
            system_id=raw.header.system_id,
            options=options,
        )

    @classmethod
    def from_windcube_data(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
        options: Options | None = None,
    ) -> Wind:
        raws = doppy.raw.WindCube.from_vad_or_dbs_srcs(data)

        if len(raws) == 0:
            raise doppy.exceptions.NoDataError("WindCube data missing")

        raw = (
            doppy.raw.WindCube.merge(raws)
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
            .reindex_scan_indices()
        )
        # select scans with most frequent elevation angle from range (15,85)
        raw = raw[(raw.elevation > 15) & (raw.elevation < 85)]
        elevation_ints = raw.elevation.round().astype(int)
        unique_elevations, counts = np.unique(elevation_ints, return_counts=True)
        most_frequent_elevation = unique_elevations[np.argmax(counts)]
        raw = raw[elevation_ints == most_frequent_elevation]

        if len(raw.time) == 0:
            raise doppy.exceptions.NoDataError("No suitable data for the wind product")

        if options and options.azimuth_offset_deg:
            raw.azimuth += options.azimuth_offset_deg

        time_list = []
        elevation_list = []
        wind_list = []
        rmse_list = []

        for scan_index in set(raw.scan_index):
            pick = raw.scan_index == scan_index
            if pick.sum() < 4:
                continue
            time_, elevation_, wind_, rmse_ = _compute_wind(raw[pick])
            time_list.append(time_)
            elevation_list.append(elevation_)
            wind_list.append(wind_[np.newaxis, :, :])
            rmse_list.append(rmse_[np.newaxis, :])

        time = np.array(time_list)
        elevation = np.array(elevation_list)
        wind = np.concatenate(wind_list)
        rmse = np.concatenate(rmse_list)
        mask = _compute_mask(wind, rmse) | np.any(np.isnan(wind), axis=2)
        if not np.allclose(elevation, elevation[0]):
            raise ValueError("Elevation is expected to stay same")
        if not (raw.height == raw.height[0]).all():
            raise ValueError("Unexpected heights")
        height = np.array(raw.height[0], dtype=np.float64)
        return Wind(
            time=time,
            height=height,
            zonal_wind=wind[:, :, 0],
            meridional_wind=wind[:, :, 1],
            vertical_wind=wind[:, :, 2],
            mask=mask,
            system_id=raw.system_id,
            options=options,
        )

    @classmethod
    def from_wls70_data(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
        options: Options | None = None,
    ) -> Wind:
        raws = doppy.raw.Wls70.from_srcs(data)

        if len(raws) == 0:
            raise doppy.exceptions.NoDataError("Wls70 data missing")

        raw = (
            doppy.raw.Wls70.merge(raws)
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
        )

        if options and options.azimuth_offset_deg:
            theta = np.deg2rad(options.azimuth_offset_deg)
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)

            meridional_wind = (
                sin_theta * raw.zonal_wind + cos_theta * raw.meridional_wind
            )
            zonal_wind = cos_theta * raw.zonal_wind - sin_theta * raw.meridional_wind
        else:
            meridional_wind = raw.meridional_wind
            zonal_wind = raw.zonal_wind

        mask = (
            np.isnan(raw.meridional_wind)
            | np.isnan(raw.zonal_wind)
            | np.isnan(raw.vertical_wind)
        )
        return Wind(
            time=raw.time,
            height=raw.altitude,
            zonal_wind=zonal_wind,
            meridional_wind=meridional_wind,
            vertical_wind=raw.vertical_wind,
            mask=mask,
            system_id=raw.system_id,
            options=options,
        )

    def write_to_netcdf(self, filename: str | Path) -> None:
        with doppy.netcdf.Dataset(filename) as nc:
            nc.add_dimension("time")
            nc.add_dimension("height")
            nc.add_time(
                name="time",
                dimensions=("time",),
                standard_name="time",
                long_name="Time UTC",
                data=self.time,
                dtype="f8",
            )
            nc.add_variable(
                name="height",
                dimensions=("height",),
                units="m",
                data=self.height,
                dtype="f4",
            )
            nc.add_variable(
                name="uwind_raw",
                dimensions=("time", "height"),
                units="m s-1",
                data=self.zonal_wind,
                mask=self.mask_zonal_wind,
                dtype="f4",
                long_name="Non-screened zonal wind",
            )
            nc.add_variable(
                name="uwind",
                dimensions=("time", "height"),
                units="m s-1",
                data=self.zonal_wind,
                mask=self.mask | self.mask_zonal_wind,
                dtype="f4",
                long_name="Zonal wind",
            )
            nc.add_variable(
                name="vwind_raw",
                dimensions=("time", "height"),
                units="m s-1",
                data=self.meridional_wind,
                mask=self.mask_meridional_wind,
                dtype="f4",
                long_name="Non-screened meridional wind",
            )
            nc.add_variable(
                name="vwind",
                dimensions=("time", "height"),
                units="m s-1",
                data=self.meridional_wind,
                mask=self.mask | self.mask_meridional_wind,
                dtype="f4",
                long_name="Meridional wind",
            )
            nc.add_attribute("serial_number", self.system_id)
            nc.add_attribute("doppy_version", doppy.__version__)
            if self.options is not None and self.options.azimuth_offset_deg is not None:
                nc.add_scalar_variable(
                    name="azimuth_offset",
                    units="degrees",
                    data=self.options.azimuth_offset_deg,
                    dtype="f4",
                    long_name="Azimuth offset of the instrument "
                    "(positive clockwise from north)",
                )


def _compute_wind(
    raw: doppy.raw.HaloHpl | doppy.raw.WindCube,
) -> tuple[float, float, npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Returns
    -------
    time

    elevation


    wind (range,component):
        Wind components for each range gate.
        Components:
        0: zonal wind
        1: meridional wind
        2: vertical wind

    rmse (range,):
        Root-mean-square error of radial velocity fit for each range gate.

    References
    ----------
    An assessment of the performance of a 1.5 µm Doppler lidar for
    operational vertical wind profiling based on a 1-year trial
        authors: E. Päschke, R. Leinweber, and V. Lehmann
        doi: 10.5194/amt-8-2251-2015
    """
    elevation = np.deg2rad(raw.elevation)
    azimuth = np.deg2rad(raw.azimuth)
    radial_velocity = raw.radial_velocity

    cos_elevation = np.cos(elevation)
    A = np.hstack(
        (
            (np.sin(azimuth) * cos_elevation).reshape(-1, 1),
            (np.cos(azimuth) * cos_elevation).reshape(-1, 1),
            (np.sin(elevation)).reshape(-1, 1),
        )
    )
    A_inv = np.linalg.pinv(A)

    w = A_inv @ radial_velocity
    r_appr = A @ w
    rmse = np.sqrt(np.sum((r_appr - radial_velocity) ** 2, axis=0) / r_appr.shape[0])
    wind = w.T
    time = raw.time[len(raw.time) // 2]
    elevation = np.round(raw.elevation)
    if not np.allclose(elevation, elevation[0]):
        raise ValueError("Elevations in the scan differ")
    return time, elevation[0], wind, rmse


def _compute_mask(
    wind: npt.NDArray[np.float64], rmse: npt.NDArray[np.float64]
) -> npt.NDArray[np.bool_]:
    """
    Parameters
    ----------

    wind (time,range,component)
    intensty (time,range)
    rmse (time,range)
    """

    def neighbour_diff(X: npt.NDArray[np.float64]) -> np.float64:
        mdiff = np.max(np.abs(X - X[len(X) // 2]))
        return np.float64(mdiff)

    WIND_NEIGHBOUR_DIFFERENCE = 20
    neighbour_mask = np.any(
        generic_filter(wind, neighbour_diff, size=(1, 3, 1))
        > WIND_NEIGHBOUR_DIFFERENCE,
        axis=2,
    )

    rmse_th = 5
    return np.array((rmse > rmse_th) | neighbour_mask, dtype=np.bool_)


def _group_scans_by_azimuth_rotation(raw: doppy.raw.HaloHpl) -> npt.NDArray[np.int64]:
    max_timedelta_in_scan = np.timedelta64(30, "s")
    if len(raw.time) < 4:
        raise doppy.exceptions.NoDataError(
            "Less than 4 profiles is not sufficient for wind product."
        )
    groups = -1 * np.ones_like(raw.time, dtype=np.int64)

    group = 0
    first_azimuth_of_scan = _wrap_and_round_angle(raw.azimuth[0])
    groups[0] = group
    for i, (time_prev, time, azimuth) in enumerate(
        zip(raw.time[:-1], raw.time[1:], raw.azimuth[1:]), start=1
    ):
        if (
            angle := _wrap_and_round_angle(azimuth)
        ) == first_azimuth_of_scan or time - time_prev > max_timedelta_in_scan:
            group += 1
            first_azimuth_of_scan = angle
        groups[i] = group
    return groups


def _wrap_and_round_angle(a: np.float64) -> int:
    return int(np.round(a)) % 360


def _select_raws_for_wind(
    raws: Sequence[doppy.raw.HaloHpl],
) -> Sequence[doppy.raw.HaloHpl]:
    counter: Counter[tuple[int, int]] = Counter()
    filtered_raws = []
    for raw in raws:
        select = (1 < raw.elevation) & (raw.elevation < 85)
        for el in arr_to_rounded_set(raw.elevation[select]):
            select_el = raw.elevation.round().astype(int) == el
            select_and = select & select_el

            if _get_nrounded_angles(raw.azimuth[select_and]) > 3:
                filtered_raws.append(raw[select_and])
                counter.update(
                    Counter(
                        (raw.header.mergeable_hash(), el)
                        for el in raw.elevation[select_and].round().astype(int)
                    )
                )
    if len(counter) == 0:
        raise doppy.exceptions.NoDataError(
            "No scans with 1 < elevation angle < 85 and more than 3 azimuth angles"
        )
    if len(counter) == 1:
        return filtered_raws
    # Else select angle closes to 75 from angles
    # that have count larger than mean_count/2
    mean_count = counter.total() / len(counter)
    elevation, _, hash = sorted(
        [
            (el, abs(el - 75), hash)
            for (hash, el), count in counter.items()
            if count > mean_count / 2
        ],
        key=lambda x: x[1],
    )[0]
    elevation_set = {elevation}
    raws = [
        raw
        for raw in filtered_raws
        if raw.header.mergeable_hash() == hash
        and arr_to_rounded_set(raw.elevation) == elevation_set
    ]
    return raws


def _get_nrounded_angles(arr: npt.NDArray[np.float64]) -> int:
    return len(set((x + 360) % 360 for x in arr_to_rounded_set(arr)))
