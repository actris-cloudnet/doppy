from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BufferedIOBase
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import numpy.typing as npt
from numpy import datetime64

import doppy
from doppy import exceptions
from doppy.utils import merge_all_equal


@dataclass
class Wls70:
    time: npt.NDArray[datetime64]  # dim: (time, )
    altitude: npt.NDArray[np.float64]  # dim: (altitude, )
    position: npt.NDArray[np.float64]  # dim: (time, )
    temperature: npt.NDArray[np.float64]  # dim: (time, )
    wiper: npt.NDArray[np.bool_]  # dim: (time, )
    cnr: npt.NDArray[np.float64]  # dim: (time, altitude)
    radial_velocity: npt.NDArray[np.float64]  # dim: (time, altitude)
    radial_velocity_deviation: npt.NDArray[np.float64]  # dim: (time, altitude)
    vh: npt.NDArray[np.float64]  # dim: (time, altitude)
    wind_direction: npt.NDArray[np.float64]  # dim: (time, altitude)
    zonal_wind: npt.NDArray[np.float64]  # u := zonal wind?, dim: (time, altitude)
    meridional_wind: npt.NDArray[
        np.float64
    ]  # v := meridional wind?, dim: (time, altitude)
    vertical_wind: npt.NDArray[np.float64]  # w := vertical wind?, dim: (time, altitude)
    system_id: str
    cnr_threshold: float

    @classmethod
    def from_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> list[Wls70]:
        if not isinstance(data, (list, tuple)):
            raise TypeError("data should be list or tuple")
        if all(isinstance(src, bytes) for src in data):
            data_bytes = data
        elif all(isinstance(src, str) for src in data):
            data_bytes = []
            for src in data:
                with Path(src).open("rb") as f:
                    data_bytes.append(f.read())
        elif all(isinstance(src, Path) for src in data):
            data_bytes = []
            for src in data:
                with src.open("rb") as f:
                    data_bytes.append(f.read())
        elif all(isinstance(src, BufferedIOBase) for src in data):
            data_bytes = [src.read() for src in data]
        else:
            raise TypeError("Unexpected types in data")
        raws = doppy.rs.raw.wls70.from_bytes_srcs(data_bytes)
        try:
            return [_raw_rs_to_wls70(r) for r in raws]
        except RuntimeError as err:
            raise exceptions.RawParsingError(err) from err

    @classmethod
    def from_src(cls, data: str | Path | bytes | BufferedIOBase) -> Wls70:
        if isinstance(data, str):
            path = Path(data)
            with path.open("rb") as f:
                data_bytes = f.read()
        elif isinstance(data, Path):
            with data.open("rb") as f:
                data_bytes = f.read()
        elif isinstance(data, bytes):
            data_bytes = data
        elif isinstance(data, BufferedIOBase):
            data_bytes = data.read()
        else:
            raise TypeError("Unsupported data type")
        try:
            return _raw_rs_to_wls70(doppy.rs.raw.wls70.from_bytes_src(data_bytes))
        except RuntimeError as err:
            raise exceptions.RawParsingError(err) from err

    def __getitem__(
        self,
        index: int
        | slice
        | list[int]
        | npt.NDArray[np.int64]
        | npt.NDArray[np.bool_]
        | tuple[slice, slice],
    ) -> Wls70:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return Wls70(
                time=self.time[index],
                altitude=self.altitude,
                position=self.position[index],
                temperature=self.temperature[index],
                wiper=self.wiper[index],
                cnr=self.cnr[index],
                radial_velocity=self.radial_velocity[index],
                radial_velocity_deviation=self.radial_velocity_deviation[index],
                vh=self.vh[index],
                wind_direction=self.wind_direction[index],
                zonal_wind=self.zonal_wind[index],
                meridional_wind=self.meridional_wind[index],
                vertical_wind=self.vertical_wind[index],
                system_id=self.system_id,
                cnr_threshold=self.cnr_threshold,
            )
        raise TypeError

    def sorted_by_time(self) -> Wls70:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    @classmethod
    def merge(cls, raws: Sequence[Wls70]) -> Wls70:
        return cls(
            time=np.concatenate(tuple(r.time for r in raws)),
            altitude=raws[0].altitude,
            position=np.concatenate(tuple(r.position for r in raws)),
            temperature=np.concatenate(tuple(r.temperature for r in raws)),
            wiper=np.concatenate(tuple(r.wiper for r in raws)),
            cnr=np.concatenate(tuple(r.cnr for r in raws)),
            radial_velocity=np.concatenate(tuple(r.radial_velocity for r in raws)),
            radial_velocity_deviation=np.concatenate(
                tuple(r.radial_velocity_deviation for r in raws)
            ),
            vh=np.concatenate(tuple(r.vh for r in raws)),
            wind_direction=np.concatenate(tuple(r.wind_direction for r in raws)),
            zonal_wind=np.concatenate(tuple(r.zonal_wind for r in raws)),
            meridional_wind=np.concatenate(tuple(r.meridional_wind for r in raws)),
            vertical_wind=np.concatenate(tuple(r.vertical_wind for r in raws)),
            system_id=merge_all_equal("system_id", [r.system_id for r in raws]),
            cnr_threshold=merge_all_equal(
                "cnr_threshold", [r.cnr_threshold for r in raws]
            ),
        )

    def non_strictly_increasing_timesteps_removed(self) -> Wls70:
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


def _raw_rs_to_wls70(
    raw_rs: tuple[dict[str, Any], list[str], npt.NDArray[np.float64]],
) -> Wls70:
    info, cols, data = raw_rs
    altitude = info["altitude"]
    system_id = info["system_id"]
    cnr_threshold = float(info["cnr_threshold"])
    data = data.reshape(-1, len(cols))
    time_ts = data[:, 0]
    time = np.array(
        [
            datetime64(datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None))
            for ts in time_ts
        ]
    )

    position = data[:, 1]
    temperature = data[:, 2]
    wiper = np.array(np.isclose(data[:, 3], 1), dtype=np.bool_)
    cnr = data[:, 4::8]
    rws = data[:, 5::8]
    rwsd = data[:, 6::8]
    vh = data[:, 7::8]
    direction = data[:, 8::8]
    u = data[:, 9::8]
    v = data[:, 10::8]
    w = data[:, 11::8]
    mask = (np.abs(u) > 90) | (np.abs(v) > 90) | (np.abs(w) > 90)
    u[mask] = np.nan
    v[mask] = np.nan
    w[mask] = np.nan
    return Wls70(
        time=time,
        altitude=altitude,
        position=position,
        temperature=temperature,
        wiper=wiper,
        cnr=cnr,
        radial_velocity=rws,
        radial_velocity_deviation=rwsd,
        vh=vh,
        wind_direction=direction,
        zonal_wind=u,
        meridional_wind=v,
        vertical_wind=w,
        system_id=system_id,
        cnr_threshold=cnr_threshold,
    )
