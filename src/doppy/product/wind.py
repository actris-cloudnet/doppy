from __future__ import annotations

import functools
from collections import defaultdict
from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence, TypeAlias

import numpy as np
import numpy.typing as npt
from scipy.ndimage import generic_filter
from sklearn.cluster import KMeans

import doppy

# ngates, gate points, elevation angle, tuple of sorted azimuth angles
SelectionGroupKeyType: TypeAlias = tuple[int, int, tuple[int, ...]]


@dataclass
class Wind:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64]
    zonal_wind: npt.NDArray[np.float64]
    meridional_wind: npt.NDArray[np.float64]
    vertical_wind: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]

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
    ) -> Wind:
        raws = doppy.raw.HaloHpl.from_srcs(data)

        if len(raws) == 0:
            raise doppy.exceptions.NoDataError("HaloHpl data missing")

        raw = (
            doppy.raw.HaloHpl.merge(_select_raws_for_wind(raws))
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
        )
        if len(raw.time) == 0:
            raise doppy.exceptions.NoDataError("No suitable data for the wind product")

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
        )

    @classmethod
    def from_windcube_data(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> Wind:
        raws = doppy.raw.WindCube.from_vad_srcs(data)

        if len(raws) == 0:
            raise doppy.exceptions.NoDataError("WindCube data missing")

        raw = (
            doppy.raw.WindCube.merge(raws)
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
            .reindex_scan_indices()
        )
        if len(raw.time) == 0:
            raise doppy.exceptions.NoDataError("No suitable data for the wind product")

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
        mask = _compute_mask(wind, rmse)
        if not np.allclose(elevation, elevation[0]):
            raise ValueError("Elevation is expected to stay same")
        height = np.array(raw.height, dtype=np.float64)
        return Wind(
            time=time,
            height=height,
            zonal_wind=wind[:, :, 0],
            meridional_wind=wind[:, :, 1],
            vertical_wind=wind[:, :, 2],
            mask=mask,
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

    def neighbour_diff(X: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        mdiff = np.max(np.abs(X - X[len(X) // 2]))
        return np.array(mdiff, dtype=np.float64)

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


def _group_scans(raw: doppy.raw.HaloHpl) -> npt.NDArray[np.int64]:
    if len(raw.time) < 4:
        raise ValueError("Expected at least 4 profiles to compute wind profile")
    if raw.time.dtype != "<M8[us]":
        raise TypeError("time expected to be in numpy datetime[us]")
    time = raw.time.astype(np.float64) * 1e-6
    timediff_in_seconds = np.diff(time)
    kmeans = KMeans(n_clusters=2, n_init="auto").fit(timediff_in_seconds.reshape(-1, 1))
    centers = kmeans.cluster_centers_.flatten()
    scanstep_timediff = centers[np.argmin(centers)]

    if scanstep_timediff < 0.1 or scanstep_timediff > 30:
        raise ValueError(
            "Time difference between profiles in one scan "
            "expected to be between 0.1 and 30 seconds"
        )
    scanstep_timediff_upperbound = 2 * scanstep_timediff
    groups_by_time = -1 * np.ones_like(time, dtype=np.int64)
    groups_by_time[0] = 0
    scan_index = 0
    for i, (t_prev, t) in enumerate(zip(time[:-1], time[1:]), start=1):
        if t - t_prev > scanstep_timediff_upperbound:
            scan_index += 1
        groups_by_time[i] = scan_index

    return _subgroup_scans(raw, groups_by_time)


def _subgroup_scans(
    raw: doppy.raw.HaloHpl, time_groups: npt.NDArray[np.int64]
) -> npt.NDArray[np.int64]:
    """
    Groups scans further based on the azimuth angles
    """
    group = -1 * np.ones_like(raw.time, dtype=np.int64)
    i = -1
    for time_group in set(time_groups):
        i += 1
        (pick,) = np.where(time_group == time_groups)
        raw_group = raw[pick]
        first_azimuth_angle = int(np.round(raw_group.azimuth[0])) % 360
        group[pick[0]] = i
        for j, azi in enumerate(
            (int(np.round(azi)) % 360 for azi in raw_group.azimuth[1:]), start=1
        ):
            if azi == first_azimuth_angle:
                i += 1
            group[pick[j]] = i
    return group


def _select_raws_for_wind(
    raws: Sequence[doppy.raw.HaloHpl],
) -> Sequence[doppy.raw.HaloHpl]:
    if len(raws) == 0:
        raise doppy.exceptions.NoDataError(
            "Cannot select raws for wind from empty list"
        )
    raws_wind = [
        raw
        for raw in raws
        if len(raw.elevation_angles) == 1
        and (el := next(iter(raw.elevation_angles))) < 80
        and el > 25
        and len(raw.azimuth_angles) > 3
    ]
    if len(raws_wind) == 0:
        raise doppy.exceptions.NoDataError(
            "No data suitable for winds: "
            "Multiple elevation angles or "
            "elevation angle >= 80 or "
            "elevation angle <= 25 or "
            "no more than 3 azimuth angles"
        )

    groups: dict[SelectionGroupKeyType, int] = defaultdict(int)

    for raw in raws_wind:
        groups[_selection_key(raw)] += len(raw.time)

    def key_func(key: SelectionGroupKeyType) -> int:
        return groups[key]

    select_tuple = max(groups, key=key_func)

    return [raw for raw in raws_wind if _selection_key(raw) == select_tuple]


def _selection_key(raw: doppy.raw.HaloHpl) -> SelectionGroupKeyType:
    if len(raw.elevation_angles) != 1:
        raise ValueError("Expected only one elevation angle")
    return (
        raw.header.mergable_hash(),
        next(iter(raw.elevation_angles)),
        tuple(sorted(raw.azimuth_angles)),
    )
