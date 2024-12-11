from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from io import BufferedIOBase
from pathlib import Path
from typing import Iterable

import numpy as np
import numpy.typing as npt
from numpy import datetime64


@dataclass
class HaloSysParams:
    time: npt.NDArray[datetime64]  # dim: (time, )
    internal_temperature: npt.NDArray[np.float64]  # dim: (time, ), unit: degree Celsius
    internal_relative_humidity: npt.NDArray[np.float64]  # dim: (time, )
    supply_voltage: npt.NDArray[np.float64]  # dim: (time, )
    acquisition_card_temperature: npt.NDArray[np.float64]  # dim: (time, )
    platform_pitch_angle: npt.NDArray[np.float64]  # dim: (time, ), unit: degrees
    platform_roll_angle: npt.NDArray[np.float64]  # dim: (time, ), unit: degrees

    @classmethod
    def from_src(cls, data: str | Path | bytes | BufferedIOBase) -> HaloSysParams:
        if isinstance(data, str):
            path = Path(data)
            with path.open("rb") as f:
                return _from_src(f)
        elif isinstance(data, Path):
            with data.open("rb") as f:
                return _from_src(f)
        elif isinstance(data, bytes):
            return _from_src(io.BytesIO(data))
        elif isinstance(data, BufferedIOBase):
            return _from_src(data)
        else:
            raise TypeError("Unsupported data type")

    @classmethod
    def merge(cls, raws: Iterable[HaloSysParams]) -> HaloSysParams:
        return cls(
            np.concatenate(tuple(r.time for r in raws)),
            np.concatenate(tuple(r.internal_temperature for r in raws)),
            np.concatenate(tuple(r.internal_relative_humidity for r in raws)),
            np.concatenate(tuple(r.supply_voltage for r in raws)),
            np.concatenate(tuple(r.acquisition_card_temperature for r in raws)),
            np.concatenate(tuple(r.platform_pitch_angle for r in raws)),
            np.concatenate(tuple(r.platform_roll_angle for r in raws)),
        )

    def __getitem__(
        self,
        index: int | slice | list[int] | npt.NDArray[np.int64] | npt.NDArray[np.bool_],
    ) -> HaloSysParams:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return HaloSysParams(
                self.time[index],
                self.internal_temperature[index],
                self.internal_relative_humidity[index],
                self.supply_voltage[index],
                self.acquisition_card_temperature[index],
                self.platform_pitch_angle[index],
                self.platform_roll_angle[index],
            )
        raise TypeError

    def sorted_by_time(self) -> HaloSysParams:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    def non_strictly_increasing_timesteps_removed(self) -> HaloSysParams:
        is_increasing = np.insert(np.diff(self.time).astype(int) > 0, 0, True)
        return self[is_increasing]


def _correct_concatenated_rows(rows: list[bytes]) -> list[bytes]:
    concat_pattern = re.compile(rb".*(\t[-+0-9]*\.[-+0-9]*\.[-+0-9]*\t).*")

    matches = [concat_pattern.fullmatch(row) for row in rows]

    if not any(matches):
        return rows
    elif not all(matches):
        raise ValueError("Cannot correct the concatenated rows")

    zero_column_pattern = re.compile(rb".*\t0\t.*")
    if not all(zero_column_pattern.fullmatch(row) for row in rows):
        raise ValueError(r"Concatenated rows are expected to have \t0\t pattern")
    rows = [row.replace(b"\t0\t", b"\t") for row in rows]

    new_rows = []
    pattern = re.compile(rb"(.*\t[-+]?[0-9]+\.[0-9]+)([-+][0-9]+\.[0-9]+\t.*)")
    pattern_nan = re.compile(rb"(.*\t)[-+]?[0-9]+\.[0-9]+\.[0-9]+(\t.*)")
    for row in rows:
        m = pattern.fullmatch(row)
        if m:
            new_rows.append(m.group(1) + b"\t" + m.group(2))
        elif m_nan := pattern_nan.fullmatch(row):
            new_rows.append(m_nan.group(1) + b"nan\tnan" + m_nan.group(2))
        else:
            raise ValueError("Cannot separate concatenated floats")
    return new_rows


def _from_src(data: BufferedIOBase) -> HaloSysParams:
    data_bytes = data.read().strip().replace(b",", b".").replace(b"\x00", b"")
    a = data_bytes.strip().split(b"\r\n")
    a = _correct_concatenated_rows(a)
    b = [r.strip().split(b"\t") for r in a]
    arr = np.array(b)
    if arr.shape[1] != 7:
        raise ValueError("Unexpected data format")

    def timestr2datetime64_12H(datetime_bytes: bytes) -> np.datetime64:
        return datetime64(
            datetime.strptime(datetime_bytes.decode("utf-8"), "%m/%d/%Y %I:%M:%S %p"),
            "s",
        )

    def timestr2datetime64_24H(datetime_bytes: bytes) -> np.datetime64:
        return datetime64(
            datetime.strptime(datetime_bytes.decode("utf-8"), "%d/%m/%Y %H:%M:%S"), "s"
        )

    arr_time = np.full_like(arr[:, 0], np.datetime64("NaT"), dtype="datetime64[s]")
    for i, time in enumerate(arr[:, 0]):
        try:
            arr_time[i] = timestr2datetime64_12H(time)
        except ValueError:
            arr_time[i] = timestr2datetime64_24H(time)
    arr_others = np.vectorize(float)(arr[:, 1:])
    return HaloSysParams(arr_time, *arr_others.T)
