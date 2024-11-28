from __future__ import annotations

from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt
from netCDF4 import Dataset, Variable, num2date
from numpy import datetime64

from doppy.utils import merge_all_equal


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
    ray_accumulation_time: np.float64  # dim: ()
    system_id: str

    @classmethod
    def from_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> list[WindCubeFixed]:
        return [WindCubeFixed.from_fixed_src(src) for src in data]

    @classmethod
    def from_fixed_src(cls, data: str | Path | bytes | BufferedIOBase) -> WindCubeFixed:
        data_bytes = _src_to_bytes(data)
        nc = Dataset("inmemory.nc", "r", memory=data_bytes)
        return _from_fixed_src(nc)

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
        return self[~np.all(np.isnan(self.cnr), axis=1)]


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
        return [WindCube.from_vad_or_dbs_src(src) for src in data]

    @classmethod
    def from_vad_or_dbs_src(cls, data: str | Path | bytes | BufferedIOBase) -> WindCube:
        data_bytes = _src_to_bytes(data)
        nc = Dataset("inmemory.nc", "r", memory=data_bytes)
        return _from_vad_or_dbs_src(nc)

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


def _src_to_bytes(data: str | Path | bytes | BufferedIOBase) -> bytes:
    if isinstance(data, str):
        path = Path(data)
        with path.open("rb") as f:
            return f.read()
    elif isinstance(data, Path):
        with data.open("rb") as f:
            return f.read()
    elif isinstance(data, bytes):
        return data
    elif isinstance(data, BufferedIOBase):
        return data.read()


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
    for _, group in enumerate(
        nc[group] for group in (nc.variables["sweep_group_name"][:])
    ):
        time_reference_ = time_reference
        if time_reference is None and "time_reference" in group.variables:
            time_reference_ = group["time_reference"][:]

        time_list.append(_extract_datetime64_or_raise(group["time"], time_reference_))
        radial_wind_speed_list.append(
            _extract_float64_or_raise(group["radial_wind_speed"], expected_dimensions)
        )
        cnr_list.append(_extract_float64_or_raise(group["cnr"], expected_dimensions))
        relative_beta_list.append(
            _extract_float64_or_raise(group["relative_beta"], expected_dimensions)
        )
        radial_wind_speed_confidence_list.append(
            _extract_float64_or_raise(
                group["radial_wind_speed_ci"], expected_dimensions
            )
        )
        azimuth_list.append(
            _extract_float64_or_raise(group["azimuth"], expected_dimensions)
        )
        elevation_list.append(
            _extract_float64_or_raise(group["elevation"], expected_dimensions)
        )
        range_list.append(
            _extract_float64_or_raise(group["range"], (expected_dimensions[1],))
        )
        doppler_spectrum_width_list.append(
            _extract_float64_or_raise(
                group["doppler_spectrum_width"], expected_dimensions
            )
        )
        ray_accumulation_time_list.append(
            _extract_float64_or_raise(
                group["ray_accumulation_time"], expected_dimensions
            )
        )

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
            np.array(ray_accumulation_time_list, dtype=np.float64).tolist(),
        ),
        system_id=nc.instrument_name,
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
    for i, group in enumerate(
        nc[group] for group in (nc.variables["sweep_group_name"][:])
    ):
        time_reference_ = time_reference
        if time_reference is None and "time_reference" in group.variables:
            time_reference_ = group["time_reference"][:]

        time_list.append(_extract_datetime64_or_raise(group["time"], time_reference_))
        radial_wind_speed_list.append(
            _extract_float64_or_raise(group["radial_wind_speed"], expected_dimensions)
        )
        cnr_list.append(_extract_float64_or_raise(group["cnr"], expected_dimensions))
        radial_wind_speed_confidence_list.append(
            _extract_float64_or_raise(
                group["radial_wind_speed_ci"], expected_dimensions
            )
        )
        azimuth_list.append(
            _extract_float64_or_raise(group["azimuth"], expected_dimensions)
        )
        elevation_list.append(
            _extract_float64_or_raise(group["elevation"], expected_dimensions)
        )
        range_list.append(
            _extract_float64_or_raise(group["range"], expected_dimensions)
        )
        height_list.append(
            _extract_float64_or_raise(group["measurement_height"], expected_dimensions)
        )
        scan_index_list.append(np.full(group["time"][:].shape, i, dtype=np.int64))

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
        system_id=nc.instrument_name,
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
) -> npt.NDArray[np.float64]:
    match nc.name:
        case "range" | "measurement_height":
            if nc.dimensions != expected_dimensions:
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "m":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.float64)
        case "cnr":
            if nc.dimensions != expected_dimensions:
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "dB":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                pass  # ignore that array contains masked values
            return _dB_to_ratio(np.array(nc[:].data, dtype=np.float64))
        case "relative_beta":
            if nc.dimensions != expected_dimensions:
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "m-1 sr-1":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                pass  # ignore that array contains masked values
            return np.array(nc[:].data, dtype=np.float64)
        case "radial_wind_speed":
            if nc.dimensions != expected_dimensions:
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "m s-1":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                pass  # ignore that array contains masked values
            return np.array(nc[:].data, dtype=np.float64)
        case "radial_wind_speed_ci":
            if nc.dimensions != expected_dimensions:
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "percent":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                pass  # ignore that array contains masked values
            return np.array(nc[:].data, dtype=np.float64)
        case "azimuth" | "elevation":
            if nc.dimensions != (expected_dimensions[0],):
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "degrees":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.float64)
        case "doppler_spectrum_width":
            if nc.dimensions != expected_dimensions:
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "m s-1":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                pass  # ignore that array contains masked values
            return np.array(nc[:].data, dtype=np.float64)
        case "ray_accumulation_time":
            if nc.dimensions != ():
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "ms":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError(f"Variable {nc.name} contains masked values")
            return np.array(nc[:].data, dtype=np.float64)
        case _:
            raise ValueError(f"Unexpected variable name {nc.name}")
