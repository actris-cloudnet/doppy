from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Callable, Sequence, TypeVar, cast

import numpy as np
import numpy.typing as npt
from netCDF4 import Dataset, Variable, num2date
from numpy import datetime64

from doppy import exceptions
from doppy.raw.utils import bytes_from_src, name_of_src
from doppy.utils import merge_all_equal

Src = str | Path | bytes | BufferedIOBase
T = TypeVar("T")

# An interrupted scan leaves a sweep group with only its settings variables.
_FIXED_VARIABLES = frozenset(
    {
        "time",
        "radial_wind_speed",
        "cnr",
        "relative_beta",
        "radial_wind_speed_ci",
        "azimuth",
        "elevation",
        "range",
        "doppler_spectrum_width",
        "ray_accumulation_time",
    }
)
_VAD_OR_DBS_VARIABLES = frozenset(
    {
        "time",
        "radial_wind_speed",
        "cnr",
        "radial_wind_speed_ci",
        "azimuth",
        "elevation",
        "range",
        "measurement_height",
    }
)


@dataclass
class WindCubeFixed:
    time: npt.NDArray[datetime64]  # dim: (time, )
    radial_distance: npt.NDArray[np.float64]  # dim: (radial_distance,)
    azimuth: npt.NDArray[np.float64]  # dim: (time, )
    elevation: npt.NDArray[np.float64]  # dim: (time, )
    cnr: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    relative_beta: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    radial_velocity: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    doppler_spectrum_width: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    radial_velocity_confidence: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    ray_accumulation_time: np.float64  # dim: (), unit: seconds
    system_id: str

    @classmethod
    def from_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> list[WindCubeFixed]:
        return _read_each(data, WindCubeFixed.from_fixed_src)

    @classmethod
    def from_fixed_src(cls, data: Src) -> WindCubeFixed:
        try:
            nc = Dataset("inmemory.nc", "r", memory=bytes_from_src(data))
            return _from_fixed_src(nc)
        except (OSError, IndexError, KeyError, AttributeError, ValueError) as err:
            raise exceptions.RawParsingError(err) from err

    @classmethod
    def merge(cls, raws: list[WindCubeFixed]) -> WindCubeFixed:
        return WindCubeFixed(
            time=np.concatenate([r.time for r in raws]),
            radial_distance=_merge_radial_distance_for_fixed(
                [r.radial_distance for r in raws]
            ),
            azimuth=np.concatenate([r.azimuth for r in raws]),
            elevation=np.concatenate([r.elevation for r in raws]),
            radial_velocity=np.concatenate([r.radial_velocity for r in raws]),
            radial_velocity_confidence=np.concatenate(
                [r.radial_velocity_confidence for r in raws]
            ),
            cnr=np.concatenate([r.cnr for r in raws]),
            relative_beta=np.concatenate([r.relative_beta for r in raws]),
            doppler_spectrum_width=np.concatenate(
                [r.doppler_spectrum_width for r in raws]
            ),
            ray_accumulation_time=merge_all_equal(
                "ray_accumulation_time", [r.ray_accumulation_time for r in raws]
            ),
            system_id=merge_all_equal("system_id", [r.system_id for r in raws]),
        )

    def __getitem__(
        self,
        index: int
        | slice
        | list[int]
        | npt.NDArray[np.int64]
        | npt.NDArray[np.bool_]
        | tuple[slice, slice],
    ) -> WindCubeFixed:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return WindCubeFixed(
                time=self.time[index],
                radial_distance=self.radial_distance,
                azimuth=self.azimuth[index],
                elevation=self.elevation[index],
                radial_velocity=self.radial_velocity[index],
                radial_velocity_confidence=self.radial_velocity_confidence[index],
                cnr=self.cnr[index],
                relative_beta=self.relative_beta[index],
                doppler_spectrum_width=self.doppler_spectrum_width[index],
                ray_accumulation_time=self.ray_accumulation_time,
                system_id=self.system_id,
            )
        raise TypeError

    def sorted_by_time(self) -> WindCubeFixed:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    def nan_profiles_removed(self) -> WindCubeFixed:
        return self[np.array(~np.all(np.isnan(self.cnr), axis=1), dtype=np.bool_)]


@dataclass
class WindCube:
    time: npt.NDArray[datetime64]  # dim: (time, )
    radial_distance: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    height: npt.NDArray[np.float64]  # dim: (time,radial_distance)
    azimuth: npt.NDArray[np.float64]  # dim: (time, )
    elevation: npt.NDArray[np.float64]  # dim: (time, )
    cnr: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    radial_velocity: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    radial_velocity_confidence: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    scan_index: npt.NDArray[np.int64]
    system_id: str

    @classmethod
    def from_vad_or_dbs_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> list[WindCube]:
        return _read_each(data, WindCube.from_vad_or_dbs_src)

    @classmethod
    def from_vad_or_dbs_src(cls, data: Src) -> WindCube:
        try:
            nc = Dataset("inmemory.nc", "r", memory=bytes_from_src(data))
            return _from_vad_or_dbs_src(nc)
        except (OSError, IndexError, KeyError, AttributeError, ValueError) as err:
            raise exceptions.RawParsingError(err) from err

    @classmethod
    def merge(cls, raws: list[WindCube]) -> WindCube:
        return WindCube(
            scan_index=_merge_scan_index([r.scan_index for r in raws]),
            time=np.concatenate([r.time for r in raws]),
            height=np.concatenate([r.height for r in raws]),
            radial_distance=np.concatenate([r.radial_distance for r in raws]),
            azimuth=np.concatenate([r.azimuth for r in raws]),
            elevation=np.concatenate([r.elevation for r in raws]),
            radial_velocity=np.concatenate([r.radial_velocity for r in raws]),
            radial_velocity_confidence=np.concatenate(
                [r.radial_velocity_confidence for r in raws]
            ),
            cnr=np.concatenate([r.cnr for r in raws]),
            system_id=merge_all_equal("system_id", [r.system_id for r in raws]),
        )

    def __getitem__(
        self,
        index: int
        | slice
        | list[int]
        | npt.NDArray[np.int64]
        | npt.NDArray[np.bool_]
        | tuple[slice, slice],
    ) -> WindCube:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return WindCube(
                time=self.time[index],
                radial_distance=self.radial_distance[index],
                height=self.height[index],
                azimuth=self.azimuth[index],
                elevation=self.elevation[index],
                radial_velocity=self.radial_velocity[index],
                radial_velocity_confidence=self.radial_velocity_confidence[index],
                cnr=self.cnr[index],
                scan_index=self.scan_index[index],
                system_id=self.system_id,
            )
        raise TypeError

    def sorted_by_time(self) -> WindCube:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    def non_strictly_increasing_timesteps_removed(self) -> WindCube:
        if len(self.time) == 0:
            return self
        mask = np.ones_like(self.time, dtype=np.bool_)
        latest_time = self.time[0]
        for i, t in enumerate(self.time[1:], start=1):
            if t <= latest_time:
                mask[i] = False
            else:
                latest_time = t
        return self[mask]

    def reindex_scan_indices(self) -> WindCube:
        new_indices = np.zeros_like(self.scan_index)
        indexed = set()
        j = 0
        for i in self.scan_index:
            if i in indexed:
                continue
            new_indices[i == self.scan_index] = j
            indexed.add(i)
            j += 1
        self.scan_index = new_indices
        return self


def _merge_scan_index(index_list: list[npt.NDArray[np.int64]]) -> npt.NDArray[np.int64]:
    if len(index_list) == 0:
        raise ValueError("cannot merge empty list")

    new_index_list = []
    current_max = index_list[0].max()
    new_index_list.append(index_list[0])

    for index_arr in index_list[1:]:
        new_arr = index_arr + current_max + 1
        new_index_list.append(new_arr)
        current_max += index_arr.max() + 1
    return np.concatenate(new_index_list)


def _merge_radial_distance_for_fixed(
    radial_distance_list: list[npt.NDArray[np.float64]],
) -> npt.NDArray[np.float64]:
    if len(radial_distance_list) == 0:
        raise ValueError("cannot merge empty list")
    if not all(
        np.allclose(arr.shape, radial_distance_list[0].shape)
        for arr in radial_distance_list
    ):
        raise ValueError("Cannot merge radial distances with different shapes")
    if not all(
        np.allclose(arr, radial_distance_list[0]) for arr in radial_distance_list
    ):
        raise ValueError("Cannot merge radial distances")
    return radial_distance_list[0]


def _read_each(
    data: Sequence[str] | Sequence[Path] | Sequence[bytes] | Sequence[BufferedIOBase],
    read: Callable[[Src], T],
) -> list[T]:
    """Read every source, skipping the ones that cannot be read.

    A day is thousands of files; one bad file should not cost the rest.
    """
    raws = []
    for src in data:
        try:
            raws.append(read(src))
        except exceptions.RawParsingError as err:
            logging.warning("Skipping %s: %s", name_of_src(src), err)
    if len(raws) < len(data):
        logging.warning("Skipped %d of %d files", len(data) - len(raws), len(data))
    return raws


def _from_fixed_src(nc: Dataset) -> WindCubeFixed:
    time_list = []
    cnr_list = []
    relative_beta_list = []
    radial_wind_speed_list = []
    radial_wind_speed_confidence_list = []
    azimuth_list = []
    elevation_list = []
    range_list = []
    doppler_spectrum_width_list = []
    ray_accumulation_time_list = []
    time_reference = (
        nc["time_reference"][:] if "time_reference" in nc.variables else None
    )

    expected_dimensions = ("time", "range")
    for name in nc.variables["sweep_group_name"][:]:
        group = nc.groups.get(name)
        if group is None or not _FIXED_VARIABLES <= set(group.variables):
            logging.debug("Skipping sweep group %s: no ray data", name)
            continue

        time_reference_ = time_reference
        if time_reference is None and "time_reference" in group.variables:
            time_reference_ = group["time_reference"][:]

        time_list.append(_extract_datetime64_or_raise(group["time"], time_reference_))
        radial_wind_speed_list.append(
            _values(
                _extract_float64_or_raise(
                    group["radial_wind_speed"], expected_dimensions
                )
            )
        )
        cnr_list.append(
            _dB_to_ratio(
                _values(_extract_float64_or_raise(group["cnr"], expected_dimensions))
            )
        )
        relative_beta_list.append(
            _values(
                _extract_float64_or_raise(group["relative_beta"], expected_dimensions)
            )
        )
        radial_wind_speed_confidence_list.append(
            _values(
                _extract_float64_or_raise(
                    group["radial_wind_speed_ci"], expected_dimensions
                )
            )
        )
        azimuth_list.append(
            _values_or_raise(
                _extract_float64_or_raise(group["azimuth"], expected_dimensions),
                "azimuth",
            )
        )
        elevation_list.append(
            _values_or_raise(
                _extract_float64_or_raise(group["elevation"], expected_dimensions),
                "elevation",
            )
        )
        range_list.append(
            _values_or_raise(
                _extract_float64_or_raise(group["range"], (expected_dimensions[1],)),
                "range",
            )
        )
        doppler_spectrum_width_list.append(
            _values(
                _extract_float64_or_raise(
                    group["doppler_spectrum_width"], expected_dimensions
                )
            )
        )
        ray_accumulation_time_list.append(
            _values_or_raise(
                _extract_float64_or_raise(
                    group["ray_accumulation_time"], expected_dimensions
                ),
                "ray_accumulation_time",
            )
            * 1e-3  # convert ms to s
        )

    if not time_list:
        raise exceptions.RawParsingError("No sweep group with ray data")

    return WindCubeFixed(
        time=np.concatenate(time_list),
        radial_distance=np.concatenate(range_list),
        azimuth=np.concatenate(azimuth_list),
        elevation=np.concatenate(elevation_list),
        radial_velocity=np.concatenate(radial_wind_speed_list),
        radial_velocity_confidence=np.concatenate(radial_wind_speed_confidence_list),
        cnr=np.concatenate(cnr_list),
        relative_beta=np.concatenate(relative_beta_list),
        doppler_spectrum_width=np.concatenate(doppler_spectrum_width_list),
        ray_accumulation_time=merge_all_equal(
            "ray_accumulation_time",
            list(np.array(ray_accumulation_time_list, dtype=np.float64)),
        ),
        system_id=_harmonised_system_id(nc.instrument_name),
    )


def _from_vad_or_dbs_src(nc: Dataset) -> WindCube:
    scan_index_list: list[npt.NDArray[np.int64]] = []
    time_list: list[npt.NDArray[np.datetime64]] = []
    cnr_list: list[npt.NDArray[np.float64]] = []
    radial_wind_speed_list: list[npt.NDArray[np.float64]] = []
    radial_wind_speed_confidence_list: list[npt.NDArray[np.float64]] = []
    azimuth_list: list[npt.NDArray[np.float64]] = []
    elevation_list: list[npt.NDArray[np.float64]] = []
    range_list: list[npt.NDArray[np.float64]] = []
    height_list: list[npt.NDArray[np.float64]] = []

    time_reference = (
        nc["time_reference"][:] if "time_reference" in nc.variables else None
    )

    expected_dimensions = ("time", "gate_index")
    scan_index = 0
    for name in nc.variables["sweep_group_name"][:]:
        group = nc.groups.get(name)
        if group is None or not _VAD_OR_DBS_VARIABLES <= set(group.variables):
            logging.debug("Skipping sweep group %s: no ray data", name)
            continue

        time_reference_ = time_reference
        if time_reference is None and "time_reference" in group.variables:
            time_reference_ = group["time_reference"][:]

        time = _extract_datetime64_or_raise(group["time"], time_reference_)
        radial_wind_speed = _extract_float64_or_raise(
            group["radial_wind_speed"], expected_dimensions
        )
        cnr = _extract_float64_or_raise(group["cnr"], expected_dimensions)
        confidence = _extract_float64_or_raise(
            group["radial_wind_speed_ci"], expected_dimensions
        )
        azimuth = _extract_float64_or_raise(group["azimuth"], expected_dimensions)
        elevation = _extract_float64_or_raise(group["elevation"], expected_dimensions)
        radial_distance = _extract_float64_or_raise(group["range"], expected_dimensions)
        height = _extract_float64_or_raise(
            group["measurement_height"], expected_dimensions
        )

        # An interrupted scan leaves fill in the positions it never measured.
        located = ~(
            _filled_rays(radial_distance)
            | _filled_rays(height)
            | _filled_rays(azimuth)
            | _filled_rays(elevation)
        )
        if not located.any():
            logging.debug("Skipping sweep group %s: no rays with a position", name)
            continue
        if not located.all():
            logging.warning(
                "Dropping %d of %d rays without a position from sweep group %s",
                int((~located).sum()),
                located.size,
                name,
            )

        time_list.append(time[located])
        radial_wind_speed_list.append(_values(radial_wind_speed)[located])
        cnr_list.append(_dB_to_ratio(_values(cnr))[located])
        radial_wind_speed_confidence_list.append(_values(confidence)[located])
        azimuth_list.append(_values(azimuth)[located])
        elevation_list.append(_values(elevation)[located])
        range_list.append(_values(radial_distance)[located])
        height_list.append(_values(height)[located])
        scan_index_list.append(np.full(int(located.sum()), scan_index, dtype=np.int64))
        scan_index += 1

    if not time_list:
        raise exceptions.RawParsingError("No sweep group with usable rays")

    return WindCube(
        scan_index=np.concatenate(scan_index_list),
        time=np.concatenate(time_list),
        radial_distance=np.concatenate(range_list),
        height=np.concatenate(height_list),
        azimuth=np.concatenate(azimuth_list),
        elevation=np.concatenate(elevation_list),
        radial_velocity=np.concatenate(radial_wind_speed_list),
        radial_velocity_confidence=np.concatenate(radial_wind_speed_confidence_list),
        cnr=np.concatenate(cnr_list),
        system_id=_harmonised_system_id(nc.instrument_name),
    )


def _extract_datetime64_or_raise(
    nc: Variable[npt.NDArray[np.float64]], time_reference: str | None
) -> npt.NDArray[np.datetime64]:
    match nc.name:
        case "time":
            if nc.dimensions != ("time",):
                raise ValueError

            units = nc.units
            if "time_reference" in nc.units:
                if time_reference is not None:
                    units = nc.units.replace("time_reference", time_reference)
                else:
                    raise ValueError("Unknown time_reference")
            return np.array(num2date(nc[:], units=units), dtype="datetime64[us]")
        case _:
            raise ValueError(f"Unexpected variable name {nc.name}")


def _dB_to_ratio(decibels: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return 10 ** (0.1 * decibels)


def _extract_float64_or_raise(
    nc: Variable[npt.NDArray[np.float64]], expected_dimensions: tuple[str, ...]
) -> np.ma.MaskedArray:
    """Validate dimensions and units, keeping the fill mask for the caller.

    Fill is expected in a measured variable, meaningless in a position.
    """
    match nc.name:
        case "range" | "measurement_height":
            dimensions, units = expected_dimensions, "m"
        case "cnr":
            dimensions, units = expected_dimensions, "dB"
        case "relative_beta":
            dimensions, units = expected_dimensions, "m-1 sr-1"
        case "radial_wind_speed" | "doppler_spectrum_width":
            dimensions, units = expected_dimensions, "m s-1"
        case "radial_wind_speed_ci":
            dimensions, units = expected_dimensions, "percent"
        case "azimuth" | "elevation":
            dimensions, units = (expected_dimensions[0],), "degrees"
        case "ray_accumulation_time":
            dimensions, units = (), "ms"
        case _:
            raise ValueError(f"Unexpected variable name {nc.name}")
    if nc.dimensions != dimensions:
        raise ValueError(f"Unexpected dimensions for {nc.name}")
    if nc.units != units:
        raise ValueError(f"Unexpected units for {nc.name}")
    return cast("np.ma.MaskedArray", nc[:])


def _values(arr: np.ma.MaskedArray) -> npt.NDArray[np.float64]:
    """Values with fill left in place."""
    return np.asarray(np.ma.getdata(arr), dtype=np.float64)


def _values_or_raise(arr: np.ma.MaskedArray, name: str) -> npt.NDArray[np.float64]:
    """Values, rejecting fill: a wrong position silently corrupts the product."""
    if np.ma.is_masked(arr):
        raise ValueError(f"Variable {name} contains masked values")
    return _values(arr)


def _filled_rays(arr: np.ma.MaskedArray) -> npt.NDArray[np.bool_]:
    """Rays holding fill anywhere; ray is the leading dimension."""
    mask = np.ma.getmaskarray(arr)
    return np.array(mask.any(axis=tuple(range(1, mask.ndim))), dtype=np.bool_)


def _harmonised_system_id(instrument_name: object) -> str:
    """The bare serial number, as the Cloudnet instrument record holds it.

    Mirrors the rule Cloudnet applies downstream. Cabauw alternates between
    WLS200S-218 and WLS200s-218 within a day, which would otherwise not merge.
    """
    # A non-string attribute is a bad file, not a crash.
    if not isinstance(instrument_name, str):
        raise ValueError(f"Unexpected instrument_name type {type(instrument_name)}")
    if match := re.match(r"wls\d+s?-(\d+)", instrument_name, re.IGNORECASE):
        return match.group(1)
    if match := re.match(r"wcs0*(\d+)", instrument_name, re.IGNORECASE):
        return match.group(1)
    return instrument_name.lstrip("0") or instrument_name
