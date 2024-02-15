from __future__ import annotations

import functools
import io
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BufferedIOBase
from os.path import commonprefix
from pathlib import Path
from typing import Any, Sequence, TypeVar, cast

import numpy as np
import numpy.typing as npt
from numpy import datetime64, timedelta64

import doppy
from doppy import exceptions

T = TypeVar("T")


@dataclass
class HaloHpl:
    header: HaloHplHeader
    time: npt.NDArray[datetime64]  # dim: (time, )
    radial_distance: npt.NDArray[np.float64]  # dim: (radial_distance, )
    azimuth: npt.NDArray[np.float64]  # dim: (time, )
    elevation: npt.NDArray[np.float64]  # dim: (time, )
    pitch: npt.NDArray[np.float64] | None  # dim: (time, )
    roll: npt.NDArray[np.float64] | None  # dim: (time, )
    radial_velocity: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    intensity: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    beta: npt.NDArray[np.float64]  # dim: (time, radial_distance)
    spectral_width: npt.NDArray[np.float64] | None  # dim: (time, radial_distance )

    @classmethod
    def from_srcs(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> list[HaloHpl]:
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
        raw_dicts = doppy.rs.raw.halo_hpl.from_bytes_srcs(data_bytes)
        try:
            return [_raw_tuple2halo_hpl(r) for r in raw_dicts]
        except RuntimeError as err:
            raise exceptions.RawParsingError(err) from err

    @classmethod
    def from_src(cls, data: str | Path | bytes | BufferedIOBase) -> HaloHpl:
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
            return _raw_tuple2halo_hpl(doppy.rs.raw.halo_hpl.from_bytes_src(data_bytes))
        except RuntimeError as err:
            raise exceptions.RawParsingError(err) from err

    @classmethod
    def _py_from_src(cls, data: str | Path | bytes | BufferedIOBase) -> HaloHpl:
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

    def __getitem__(
        self,
        index: int
        | slice
        | list[int]
        | npt.NDArray[np.int64]
        | npt.NDArray[np.bool_]
        | tuple[slice, slice],
    ) -> HaloHpl:
        if isinstance(index, (int, slice, list, np.ndarray)):
            return HaloHpl(
                header=self.header,
                time=self.time[index],
                radial_distance=self.radial_distance,
                azimuth=self.azimuth[index],
                elevation=self.elevation[index],
                radial_velocity=self.radial_velocity[index],
                intensity=self.intensity[index],
                beta=self.beta[index],
                pitch=self.pitch[index] if self.pitch is not None else None,
                roll=self.roll[index] if self.roll is not None else None,
                spectral_width=self.spectral_width[index]
                if self.spectral_width is not None
                else None,
            )
        raise TypeError

    @classmethod
    def merge(cls, raws: Sequence[HaloHpl]) -> HaloHpl:
        return cls(
            header=_merge_headers([r.header for r in raws]),
            time=np.concatenate(tuple(r.time for r in raws)),
            radial_distance=raws[0].radial_distance,
            azimuth=np.concatenate(tuple(r.azimuth for r in raws)),
            elevation=np.concatenate(tuple(r.elevation for r in raws)),
            radial_velocity=np.concatenate(tuple(r.radial_velocity for r in raws)),
            intensity=np.concatenate(tuple(r.intensity for r in raws)),
            beta=np.concatenate(tuple(r.beta for r in raws)),
            pitch=_merge_float_arrays_or_nones(tuple(r.pitch for r in raws)),
            roll=_merge_float_arrays_or_nones(tuple(r.roll for r in raws)),
            spectral_width=_merge_float_arrays_or_nones(
                tuple(r.spectral_width for r in raws)
            ),
        )

    @functools.cached_property
    def azimuth_angles(self) -> set[int]:
        return set(int(x) % 360 for x in np.round(self.azimuth))

    @functools.cached_property
    def elevation_angles(self) -> set[int]:
        return set(int(x) for x in np.round(self.elevation))

    @functools.cached_property
    def time_diffs(self) -> set[int]:
        return set(np.diff(self.time.astype("datetime64[s]").astype("int")))

    @functools.cached_property
    def median_time_diff(self) -> float:
        med = np.round(
            np.median(
                np.diff(1e-6 * self.time.astype("datetime64[us]").astype("float"))
            ),
            2,
        )
        if isinstance(med, float):
            return med
        raise TypeError

    def sorted_by_time(self) -> HaloHpl:
        sort_indices = np.argsort(self.time)
        return self[sort_indices]

    def non_strictly_increasing_timesteps_removed(self) -> HaloHpl:
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


@dataclass(slots=True)
class HaloHplHeader:
    filename: str
    gate_points: int
    nrays: int | None
    nwaypoints: int | None
    ngates: int
    pulses_per_ray: int
    range_gate_length: float
    resolution: float
    scan_type: str
    focus_range: int
    start_time: datetime64
    system_id: str
    instrument_spectral_width: float | None

    def mergable_hash(self) -> int:
        return hash(
            (
                self.gate_points,
                self.nrays,
                self.nwaypoints,
                self.ngates,
                self.pulses_per_ray,
                round(self.range_gate_length, 1),
                round(self.resolution, 1),
                self.scan_type,
                self.focus_range,
                self.system_id,
                round(x, 1)
                if isinstance((x := self.instrument_spectral_width), float)
                else None,
            )
        )

    @classmethod
    def from_dict(cls, data: dict[bytes, bytes]) -> HaloHplHeader:
        return cls(
            filename=data[b"Filename"].decode(),
            gate_points=int(data[b"Gate length (pts)"]),
            nrays=(
                int(data[b"No. of rays in file"])
                if b"No. of rays in file" in data
                else None
            ),
            nwaypoints=(
                int(data[b"No. of waypoints in file"])
                if b"No. of waypoints in file" in data
                else None
            ),
            ngates=int(data[b"Number of gates"]),
            pulses_per_ray=int(data[b"Pulses/ray"]),
            range_gate_length=float(data[b"Range gate length (m)"]),
            resolution=float(data[b"Resolution (m/s)"]),
            scan_type=data[b"Scan type"].decode(),
            focus_range=int(data[b"Focus range"]),
            start_time=_parser_start_time(data[b"Start time"]),
            system_id=data[b"System ID"].decode(),
            instrument_spectral_width=(
                float(data[b"instrument_spectral_width"])
                if b"instrument_spectral_width" in data
                else None
            ),
        )


def _merger(key: str, lst: list[T]) -> T:
    if len(set(lst)) != 1:
        raise ValueError(f"Cannot merge header key {key} values {lst}")
    return lst[0]


def _merge_headers(headers: list[HaloHplHeader]) -> HaloHplHeader:
    return HaloHplHeader(
        filename=commonprefix([h.filename for h in headers]),
        start_time=np.min([h.start_time for h in headers]),
        **{
            key: _merger(key, [getattr(h, key) for h in headers])
            for key in (
                "gate_points",
                "nrays",
                "nwaypoints",
                "ngates",
                "pulses_per_ray",
                "range_gate_length",
                "resolution",
                "scan_type",
                "focus_range",
                "system_id",
                "instrument_spectral_width",
            )
        },
    )


def _merge_float_arrays_or_nones(
    arrs: tuple[npt.NDArray[np.float64] | None, ...],
) -> npt.NDArray[np.float64] | None:
    isnone = tuple(x is None for x in arrs)
    if all(isnone):
        return None
    if any(isnone):
        raise ValueError
    arrs = cast(tuple[npt.NDArray[np.float64], ...], arrs)
    return np.concatenate(arrs, axis=0)


def _raw_tuple2halo_hpl(
    raw_tuple: tuple[dict[str, Any], dict[str, npt.NDArray[np.float64] | None]],
) -> HaloHpl:
    header_dict, data_dict = raw_tuple
    header = HaloHplHeader(
        filename=str(header_dict["filename"]),
        gate_points=int(header_dict["gate_points"]),
        nrays=int(header_dict["nrays"]) if header_dict["nrays"] is not None else None,
        nwaypoints=int(header_dict["nwaypoints"])
        if header_dict["nwaypoints"] is not None
        else None,
        ngates=int(header_dict["ngates"]),
        pulses_per_ray=int(header_dict["pulses_per_ray"]),
        range_gate_length=float(header_dict["range_gate_length"]),
        resolution=float(header_dict["resolution"]),
        scan_type=str(header_dict["scan_type"]),
        focus_range=int(header_dict["focus_range"]),
        start_time=datetime64(datetime.utcfromtimestamp(header_dict["start_time"])),
        system_id=str(header_dict["system_id"]),
        instrument_spectral_width=float(header_dict["instrument_spectral_width"])
        if header_dict["instrument_spectral_width"] is not None
        else None,
    )
    expected_range = np.arange(header.ngates, dtype=np.float64)

    if any(
        data_dict[key] is None
        for key in (
            "range",
            "time",
            "radial_distance",
            "azimuth",
            "elevation",
            "radial_velocity",
            "intensity",
            "beta",
        )
    ):
        raise TypeError
    range_ = cast(npt.NDArray[np.float64], data_dict["range"]).reshape(
        -1, header.ngates
    )
    radial_distance = cast(npt.NDArray[np.float64], data_dict["radial_distance"])
    azimuth = cast(npt.NDArray[np.float64], data_dict["azimuth"])
    elevation = cast(npt.NDArray[np.float64], data_dict["elevation"])
    radial_velocity = cast(
        npt.NDArray[np.float64], data_dict["radial_velocity"]
    ).reshape(-1, header.ngates)
    intensity = cast(npt.NDArray[np.float64], data_dict["intensity"]).reshape(
        -1, header.ngates
    )
    beta = cast(npt.NDArray[np.float64], data_dict["beta"]).reshape(-1, header.ngates)
    if not np.isclose(range_, expected_range).all():
        raise exceptions.RawParsingError(
            "Incoherent range gates: Number of gates in the middle of the file"
        )
    return HaloHpl(
        header=header,
        time=_convert_time(
            header.start_time, cast(npt.NDArray[np.float64], data_dict["time"])
        ),
        radial_distance=radial_distance,
        azimuth=azimuth,
        elevation=elevation,
        pitch=data_dict["pitch"] if data_dict["pitch"] is not None else None,
        roll=data_dict["roll"] if data_dict["roll"] is not None else None,
        radial_velocity=radial_velocity,
        intensity=intensity,
        beta=beta,
        spectral_width=data_dict["spectral_width"].reshape(-1, header.ngates)
        if data_dict["spectral_width"] is not None
        else None,
    )


def _convert_time(
    start_time: datetime64, decimal_time: npt.NDArray[np.float64]
) -> npt.NDArray[datetime64]:
    """
    Parameters
    ----------
    start_time: unix-time
    decimal_time: hours since beginning of the day of start_time
    """
    HOURS_TO_MICROSECONDS = 3600000000.0
    start_of_day = datetime64(start_time, "D").astype("datetime64[us]")
    delta_hours = (decimal_time * HOURS_TO_MICROSECONDS).astype("timedelta64[us]")
    return np.array(start_of_day + delta_hours, dtype=datetime64)


def _parser_start_time(s: bytes) -> datetime64:
    return datetime64(datetime.strptime(s.decode(), "%Y%m%d %H:%M:%S.%f"))


def _from_src(data: BufferedIOBase) -> HaloHpl:
    head = data.read(1000)
    match_header_div = re.search(b"\\*\\*\\*\\*.*\n+", head, re.MULTILINE)
    if match_header_div is None:
        raise exceptions.RawParsingError("Cannot find header divider '****'")
    data.seek(0)
    _, div = match_header_div.span()
    header_bytes = data.read(div)
    header = _read_header(header_bytes)
    data_bytes = data.read()
    res = _read_data(data_bytes, header)
    return res


def _read_header(data: bytes) -> HaloHplHeader:
    data = data.strip()
    data_dict = {}
    expected_header_rows = [
        b"Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length",
        b"Range of measurement (center of gate) = (range gate + 0.5) * Gate length",
        b"Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) "
        b"Pitch (degrees) Roll (degrees)",
        b"Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees)",
        b"f9.6,1x,f6.2,1x,f6.2",
        b"Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)",
        b"Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1) "
        b"Spectral Width",
        b"i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates",
        b"i3,1x,f6.4,1x,f8.6,1x,e12.6,1x,f6.4 - repeat for no. gates",
        b"****",
    ]
    for line in data.split(b"\r\n"):
        split = line.split(b":\t")
        if len(split) == 2:
            key, val = split
            data_dict[key] = val
        else:
            (val,) = split
            if m := re.match(rb"\*\*\*\* Instrument spectral width = (.*)", val):
                data_dict[b"instrument_spectral_width"] = m.group(1)
            elif val not in expected_header_rows:
                raise ValueError(f"Unexpected row '{val!r}'")
    return HaloHplHeader.from_dict(data_dict)


def _read_data(data: bytes, header: HaloHplHeader) -> HaloHpl:
    if not data:
        raise exceptions.RawParsingError("No data found")
    data = data.strip()
    data = data.replace(
        b"\x00", b""
    )  # Some files contain null characters between profiles
    data_lines = data.split(b"\r\n")

    i = 0
    while i + 1 < len(data_lines) and data_lines[i + 1].strip().split()[0] != b"0":
        i += 1
    del data_lines[:i]

    i = len(data_lines) - 1
    while (
        i - 1 >= 0
        and header.ngates > 1
        and len(data_lines[i].strip().split()) != len(data_lines[i - 1].strip().split())
    ):
        i -= 1
    del data_lines[i + 1 :]

    trailing_lines = len(data_lines) % (header.ngates + 1)
    if trailing_lines > 0:
        del data_lines[-trailing_lines:]

    data1D_lines = data_lines[:: header.ngates + 1]
    data1D = [list(map(float, line.split())) for line in data1D_lines]
    try:
        data1Darr = np.array(data1D)
    except ValueError as err:
        if "inhomogeneous" in str(err):
            raise exceptions.RawParsingError(
                "Inhomogeneous raw data. "
                "Probable reason: Number of gates changes in middle of the file"
            ) from err
        else:
            raise

    del data_lines[:: header.ngates + 1]
    data2D = [list(map(float, line.split())) for line in data_lines]
    data2Darr = np.array(data2D)

    decimal_time = data1Darr[:, 0]
    time = header.start_time.astype("datetime64[D]") + np.array(
        list(map(_decimal_time2timedelta, decimal_time))
    )
    azimuth = data1Darr[:, 1]
    elevation = data1Darr[:, 2]
    pitch = data1Darr[:, 3] if data1Darr.shape[1] > 3 else None
    roll = data1Darr[:, 4] if data1Darr.shape[1] > 4 else None

    ntimes = len(decimal_time)

    data2Darr_reshape = data2Darr.reshape(ntimes, header.ngates, -1)

    gate = data2Darr_reshape[:, :, 0]
    gate_expected = np.arange(len(gate[0])).astype("float64")
    if not all(np.allclose(gate_expected, gate[i, :]) for i in range(gate.shape[0])):
        raise ValueError("all gate indices should be equal")
    radial_distance = (gate_expected + 0.5) * header.range_gate_length

    radial_velocity = data2Darr_reshape[:, :, 1]
    intensity = data2Darr_reshape[:, :, 2]
    beta = data2Darr_reshape[:, :, 3]

    spectral_width = (
        data2Darr_reshape[:, :, 4] if data2Darr_reshape.shape[2] > 4 else None
    )

    return HaloHpl(
        header,
        time,
        radial_distance,
        azimuth,
        elevation,
        pitch,
        roll,
        radial_velocity,
        intensity,
        beta,
        spectral_width,
    )


def _decimal_time2timedelta(h: float) -> timedelta64:
    return timedelta64(timedelta(hours=h))
