from __future__ import annotations

from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt
from netCDF4 import Dataset, num2date
from numpy import datetime64


@dataclass
class WindCube:
    time: npt.NDArray[datetime64]  # dim: (time, )
    radial_distance: npt.NDArray[np.int64]  # dim: (radial_distance, )
    height: npt.NDArray[np.int64]  # dim: (radial_distance, )
    azimuth: npt.NDArray[np.float64]  # dim: (time, )
    elevation: npt.NDArray[np.float64]  # dim: (time, )
    cnr: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    radial_velocity: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    radial_velocity_confidence: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    scan_index: npt.NDArray[np.int64]

    @classmethod
    def from_vad_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> list[WindCube]:
        return [WindCube.from_vad_src(src) for src in data]

    @classmethod
    def from_vad_src(cls, data: str | Path | bytes | BufferedIOBase) -> WindCube:
        data_bytes = _src_to_bytes(data)
        nc = Dataset("inmemory.nc", "r", memory=data_bytes)
        return _from_vad_src(nc)

    @classmethod
    def merge(cls, raws: list[WindCube]) -> WindCube:
        return WindCube(
            scan_index=_merge_scan_index([r.scan_index for r in raws]),
            time=np.concatenate([r.time for r in raws]),
            height=_merge_range_vars([r.height for r in raws]),
            radial_distance=_merge_range_vars([r.radial_distance for r in raws]),
            azimuth=np.concatenate([r.azimuth for r in raws]),
            elevation=np.concatenate([r.elevation for r in raws]),
            radial_velocity=np.concatenate([r.radial_velocity for r in raws]),
            radial_velocity_confidence=np.concatenate(
                [r.radial_velocity_confidence for r in raws]
            ),
            cnr=np.concatenate([r.cnr for r in raws]),
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
                radial_distance=self.radial_distance,
                height=self.height,
                azimuth=self.azimuth[index],
                elevation=self.elevation[index],
                radial_velocity=self.radial_velocity[index],
                radial_velocity_confidence=self.radial_velocity_confidence[index],
                cnr=self.cnr[index],
                scan_index=self.scan_index[index],
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


def _merge_range_vars(vars: list[npt.NDArray[np.int64]]) -> npt.NDArray[np.int64]:
    var = np.concatenate([v[np.newaxis, :] for v in vars])
    if not (var[0] == var).all():
        raise ValueError("Cannot merge unequal range variable")
    return np.array(var[0], dtype=np.int64)


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
    raise TypeError("Unsupported data type")


def _from_vad_src(nc: Dataset) -> WindCube:
    scan_index_list = []
    time_list = []
    cnr_list = []
    radial_wind_speed_list = []
    radial_wind_speed_confidence_list = []
    azimuth_list = []
    elevation_list = []
    range_list = []
    height_list = []

    for i, group in enumerate(
        nc[group] for group in (nc.variables["sweep_group_name"][:])
    ):
        time_list.append(_extract_datetime64_or_raise(group["time"]))
        radial_wind_speed_list.append(
            _extract_float64_or_raise(group["radial_wind_speed"])
        )
        cnr_list.append(_extract_float64_or_raise(group["cnr"]))
        radial_wind_speed_confidence_list.append(
            _extract_float64_or_raise(group["radial_wind_speed_ci"])
        )
        azimuth_list.append(_extract_float64_or_raise(group["azimuth"]))
        elevation_list.append(_extract_float64_or_raise(group["elevation"]))
        range_list.append(_extract_int64_or_raise(group["range"]))
        height_list.append(_extract_int64_or_raise(group["measurement_height"]))
        scan_index_list.append(np.full(group["time"][:].shape, i, dtype=np.int64))

    height = np.concatenate(height_list)
    if not (height == height[0]).all():
        raise ValueError("Unexpected heights")
    radial_distance = np.concatenate(range_list)
    if not (radial_distance == radial_distance[0]).all():
        raise ValueError("Unexpected range")
    return WindCube(
        scan_index=np.concatenate(scan_index_list),
        time=np.concatenate(time_list),
        radial_distance=radial_distance[0],
        height=height[0],
        azimuth=np.concatenate(azimuth_list),
        elevation=np.concatenate(elevation_list),
        radial_velocity=np.concatenate(radial_wind_speed_list),
        radial_velocity_confidence=np.concatenate(radial_wind_speed_confidence_list),
        cnr=np.concatenate(cnr_list),
    )


def _extract_datetime64_or_raise(nc: Dataset) -> npt.NDArray[np.datetime64]:
    match nc.name:
        case "time":
            if nc.dimensions != ("time",):
                raise ValueError
            return np.array(num2date(nc[:], units=nc.units), dtype="datetime64[us]")
        case _:
            raise ValueError(f"Unexpected variable name {nc.name}")


def _extract_float64_or_raise(nc: Dataset) -> npt.NDArray[np.float64]:
    match nc.name:
        case "cnr":
            if nc.dimensions != ("time", "gate_index"):
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "dB":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.float64)
        case "radial_wind_speed":
            if nc.dimensions != ("time", "gate_index"):
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "m s-1":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.float64)
        case "radial_wind_speed_ci":
            if nc.dimensions != ("time", "gate_index"):
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "percent":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.float64)
        case "azimuth" | "elevation":
            if nc.dimensions != ("time",):
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "degrees":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.float64)
        case _:
            raise ValueError(f"Unexpected variable name {nc.name}")


def _extract_int64_or_raise(nc: Dataset) -> npt.NDArray[np.int64]:
    match nc.name:
        case "range" | "measurement_height":
            if nc.dimensions != ("time", "gate_index"):
                raise ValueError(f"Unexpected dimensions for {nc.name}")
            if nc.units != "m":
                raise ValueError(f"Unexpected units for {nc.name}")
            if nc[:].mask is not np.bool_(False):
                raise ValueError
            return np.array(nc[:].data, dtype=np.int64)
        case _:
            raise ValueError(f"Unexpected variable name {nc.name}")
