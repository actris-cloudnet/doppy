from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt
from numpy import datetime64


@dataclass
class HaloBg:
    time: npt.NDArray[datetime64]  # dim: (time, )
    signal: npt.NDArray[np.float64]  # dim: (time, range)

    @property
    def ngates(self) -> int:
        return int(self.signal.shape[1])

    @classmethod
    def from_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[tuple[bytes, str]]
        | Sequence[tuple[BufferedIOBase, str]],
    ) -> list[HaloBg]:
        if not isinstance(data, (list, tuple)):
            raise TypeError("data should be list or tuple")
        # TODO: rust reader and proper type checking
        data_normalised = []
        for item in data:
            if isinstance(item, str):
                path = Path(item)
                with path.open("rb") as f:
                    data_normalised.append((f.read(), path.name))
            elif isinstance(item, Path):
                with item.open("rb") as f:
                    data_normalised.append((f.read(), item.name))
            elif isinstance(item, tuple) and isinstance(item[0], bytes):
                data_normalised.append(item)
            elif isinstance(item, tuple) and isinstance(item[0], BufferedIOBase):
                data_normalised.append((item[0].read(), item[1]))
        return [
            HaloBg.from_src(data_bytes, filename)
            for data_bytes, filename in data_normalised
        ]

    @classmethod
    def from_src(
        cls, data: str | Path | bytes | BufferedIOBase, filename: str | None = None
    ) -> HaloBg:
        if isinstance(data, str):
            path = Path(data)
            if filename is None:
                filename = path.name
            with path.open("rb") as f:
                return _from_src(f, filename)
        elif isinstance(data, Path):
            if filename is None:
                filename = data.name
            with data.open("rb") as f:
                return _from_src(f, filename)
        elif isinstance(data, bytes):
            if filename is None:
                raise TypeError("Filename is mandatory if data is given as bytes")
            return _from_src(io.BytesIO(data), filename)
        elif isinstance(data, BufferedIOBase):
            if filename is None:
                raise TypeError(
                    "Filename is mandatory if data is given as BufferedIOBase"
                )
            return _from_src(data, filename)
        else:
            raise TypeError("Unsupported data type")

    @classmethod
    def merge(cls, raws: Sequence[HaloBg]) -> HaloBg:
        return cls(
            np.concatenate(tuple(r.time for r in raws)),
            np.concatenate(tuple(r.signal for r in raws)),
        )

    def __getitem__(
        self,
        index: int
        | slice
        | list[int]
        | npt.NDArray[np.int64]
        | npt.NDArray[np.bool_]
        | tuple[slice, slice],
    ) -> HaloBg:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return HaloBg(self.time[index], self.signal[index])
        elif isinstance(index, tuple):
            return HaloBg(self.time[index[0]], self.signal[index])
        raise TypeError

    def sorted_by_time(self) -> HaloBg:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    def non_strictly_increasing_timesteps_removed(self) -> HaloBg:
        is_increasing = np.insert(np.diff(self.time).astype(int) > 0, 0, True)
        return self[is_increasing]


def _from_src(data: BufferedIOBase, filename: str) -> HaloBg:
    if not (m := re.match(r"^Background_(\d{6}-\d{6}).txt", filename)):
        raise ValueError(f"Cannot parse datetime from filename: {filename}")
    time = np.array(datetime64(datetime.strptime(m.group(1), "%d%m%y-%H%M%S")))[
        np.newaxis
    ]

    data_bytes = data.read().strip()
    if b"\r\n" not in data_bytes:
        signal = _from_src_without_newlines(data_bytes)
    else:
        try:
            signal = np.array(list(map(float, data_bytes.split(b"\r\n"))))[np.newaxis]
        except ValueError:
            signal = np.array(
                list(map(float, data_bytes.replace(b",", b".").split(b"\r\n")))
            )[np.newaxis]
    return HaloBg(time, signal)


def _from_src_without_newlines(data: bytes) -> npt.NDArray[np.float64]:
    NUMBER_OF_DECIMALS = 6
    match = re.finditer(rb"\.", data)
    start = 0
    signal = []
    for i in match:
        end = i.end() + NUMBER_OF_DECIMALS
        signal.append(float(data[start:end]))
        start = end
    return np.array(signal)[np.newaxis]
