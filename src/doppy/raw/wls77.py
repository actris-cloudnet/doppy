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
from doppy.raw.utils import bytes_from_src
from doppy.utils import merge_all_equal


@dataclass
class Wls77:
    time: npt.NDArray[datetime64]  # dim: (time, )
    altitude: npt.NDArray[np.float64]  # dim: (altitude, )
    position: npt.NDArray[np.float64]  # dim: (time, )
    temperature: npt.NDArray[np.float64]  # dim: (time, )
    wiper_count: npt.NDArray[np.float64]  # dim: (time, )
    cnr: npt.NDArray[np.float64]  # dim: (time, altitude)
    radial_velocity: npt.NDArray[np.float64]  # dim: (time, altitude)
    radial_velocity_deviation: npt.NDArray[np.float64]  # dim: (time, altitude)
    wind_speed: npt.NDArray[np.float64]  # dim: (time, altitude)
    wind_direction: npt.NDArray[np.float64]  # dim: (time, altitude)
    zonal_wind: npt.NDArray[np.float64]  # u := zonal wind?, dim: (time, altitude)
    meridional_wind: npt.NDArray[
        np.float64
    ]  # v := meridional wind?, dim: (time, altitude)
    vertical_wind: npt.NDArray[np.float64]  # w := vertical wind?, dim: (time, altitude)
    cnr_threshold: float
    system_id: str

    @classmethod
    def from_srcs(
        cls, data: Sequence[str | bytes | Path | BufferedIOBase]
    ) -> list[Wls77]:
        data_bytes = [bytes_from_src(src) for src in data]
        raws = doppy.rs.raw.wls77.from_bytes_srcs(data_bytes)
        try:
            return [_raw_rs_to_wls77(r) for r in raws]
        except RuntimeError as err:
            raise exceptions.RawParsingError(err) from err

    @classmethod
    def from_src(cls, data: str | Path | bytes | BufferedIOBase) -> Wls77:
        data_bytes = bytes_from_src(data)
        try:
            return _raw_rs_to_wls77(doppy.rs.raw.wls77.from_bytes_src(data_bytes))
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
    ) -> Wls77:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return Wls77(
                time=self.time[index],
                altitude=self.altitude,
                position=self.position[index],
                temperature=self.temperature[index],
                wiper_count=self.wiper_count[index],
                cnr=self.cnr[index],
                radial_velocity=self.radial_velocity[index],
                radial_velocity_deviation=self.radial_velocity_deviation[index],
                wind_speed=self.wind_speed[index],
                wind_direction=self.wind_direction[index],
                zonal_wind=self.zonal_wind[index],
                meridional_wind=self.meridional_wind[index],
                vertical_wind=self.vertical_wind[index],
                system_id=self.system_id,
                cnr_threshold=self.cnr_threshold,
            )
        raise TypeError

    def sorted_by_time(self) -> Wls77:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    @classmethod
    def merge(cls, raws: Sequence[Wls77]) -> Wls77:
        return cls(
            time=np.concatenate(tuple(r.time for r in raws)),
            altitude=raws[0].altitude,
            position=np.concatenate(tuple(r.position for r in raws)),
            temperature=np.concatenate(tuple(r.temperature for r in raws)),
            wiper_count=np.concatenate(tuple(r.wiper_count for r in raws)),
            cnr=np.concatenate(tuple(r.cnr for r in raws)),
            radial_velocity=np.concatenate(tuple(r.radial_velocity for r in raws)),
            radial_velocity_deviation=np.concatenate(
                tuple(r.radial_velocity_deviation for r in raws)
            ),
            wind_speed=np.concatenate(tuple(r.wind_speed for r in raws)),
            wind_direction=np.concatenate(tuple(r.wind_direction for r in raws)),
            zonal_wind=np.concatenate(tuple(r.zonal_wind for r in raws)),
            meridional_wind=np.concatenate(tuple(r.meridional_wind for r in raws)),
            vertical_wind=np.concatenate(tuple(r.vertical_wind for r in raws)),
            system_id=merge_all_equal("system_id", [r.system_id for r in raws]),
            cnr_threshold=merge_all_equal(
                "cnr_threshold", [r.cnr_threshold for r in raws]
            ),
        )

    def non_strictly_increasing_timesteps_removed(self) -> Wls77:
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


def _raw_rs_to_wls77(
    raw: dict[str, Any],
) -> Wls77:
    time_ts = raw["time"]
    time = np.array(
        [
            datetime64(datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None))
            for ts in time_ts
        ]
    )

    n = time.size

    return Wls77(
        time=time,
        altitude=np.array(raw["altitude"], dtype=np.float64),
        position=np.array(raw["position"], dtype=np.float64),
        temperature=np.array(raw["temperature"], dtype=np.float64),
        wiper_count=np.array(raw["wiper_count"], dtype=np.float64),
        cnr=np.array(raw["cnr"], dtype=np.float64).reshape(n, -1),
        radial_velocity=np.array(raw["radial_velocity"], dtype=np.float64).reshape(
            n, -1
        ),
        radial_velocity_deviation=np.array(
            raw["radial_velocity_deviation"], dtype=np.float64
        ).reshape(n, -1),
        wind_speed=np.array(raw["wind_speed"], dtype=np.float64).reshape(n, -1),
        wind_direction=np.array(raw["wind_direction"], dtype=np.float64).reshape(n, -1),
        zonal_wind=np.array(raw["zonal_wind"], dtype=np.float64).reshape(n, -1),
        meridional_wind=np.array(raw["meridional_wind"], dtype=np.float64).reshape(
            n, -1
        ),
        vertical_wind=np.array(raw["vertical_wind"], dtype=np.float64).reshape(n, -1),
        cnr_threshold=raw["cnr_threshold"],
        system_id=raw["system_id"],
    )
