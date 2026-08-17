from __future__ import annotations

import argparse
import dataclasses
import datetime
import gzip
import logging
import re
import shutil
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import requests
import scipy.constants
from matplotlib.axes import Axes
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

import doppy
import doppy.options
from doppy.product import Stare, StareDepol, Wind, WindOptions
from doppy.product.stare import PulsesPerRay, RayAccumulationTime
from doppy.product.turbulence import (
    HorizontalWind,
    Turbulence,
    VerticalWind,
)
from doppy.product.turbulence import Options as TurbOptions
from doppy.raw import (
    HaloBg,
    HaloHpl,
    HaloSysParams,
    WindCube,
    WindCubeFixed,
    Wls70,
    Wls77,
)

API_BASE = "https://cloudnet.fmi.fi/api"
CACHE_ROOT = Path(__file__).resolve().parent.parent / "data" / "_cloudnet_cache"

# cloudnetpy.products.epsilon_lidar hardcodes a 3-minute variance window,
# overriding doppy's 600 s default.
EPSILON_WINDOW_SECONDS = 3 * 60
ZENITH_ANGLE_THRESHOLD = 15

PRODUCT_INSTRUMENT_PRIORITY: dict[str, list[str]] = {
    "stare": ["halo-doppler-lidar", "wls200s", "wls400s"],
    "wind": ["halo-doppler-lidar", "wls200s", "wls400s", "wls70", "wls77"],
    "turbulence": ["halo-doppler-lidar"],
    "raw": ["halo-doppler-lidar", "wls200s", "wls400s", "wls70", "wls77"],
}


# ---------------------------------------------------------------- raw-files API


@dataclass
class RawRec:
    uuid: str
    filename: str
    measurement_date: datetime.date
    tags: frozenset[str]
    instrument_id: str
    instrument_pid: str
    site_altitude: float
    download_url: str
    size: int


@dataclass(frozen=True)
class Instrument:
    """One deployed unit. Cloudnet keys processing on the PID, not the id —
    the id only names the model, so a site running two of them needs the PID
    to keep their uploads apart, and calibrations are stored per PID."""

    id: str
    pid: str
    site_altitude: float


def _row_to_rec(row: dict) -> RawRec:
    return RawRec(
        uuid=row["uuid"],
        filename=row["filename"],
        measurement_date=datetime.date.fromisoformat(row["measurementDate"]),
        tags=frozenset(row.get("tags") or []),
        instrument_id=row["instrument"]["instrumentId"],
        instrument_pid=row["instrument"]["pid"],
        site_altitude=float(row["site"]["altitude"]),
        download_url=row["downloadUrl"],
        size=int(row.get("size", 0)),
    )


def fetch_raw_records(
    session: requests.Session,
    site: str,
    date_from: datetime.date,
    date_to: datetime.date,
    instrument: str | None,
    instrument_pid: str | None = None,
) -> list[RawRec]:
    params: dict[str, str | list[str]] = {
        "site": site,
        "dateFrom": date_from.isoformat(),
        "dateTo": date_to.isoformat(),
        "status": ["uploaded", "processed"],
    }
    if instrument is not None:
        params["instrument"] = instrument
    if instrument_pid is not None:
        params["instrumentPid"] = instrument_pid
    resp = session.get(f"{API_BASE}/raw-files", params=params, timeout=60)
    resp.raise_for_status()
    return [_row_to_rec(row) for row in resp.json()]


# ---------------------------------------------------------------- calibration


@dataclass(frozen=True)
class Calibration:
    """The doppler-lidar keys of /api/calibration, resolved to doppy options."""

    time_offset: datetime.timedelta | None
    noise_mask_method: doppy.options.NoiseMaskMethod
    wind_options: WindOptions | None

    def describe(self) -> str:
        parts = []
        if self.time_offset is not None:
            parts.append(f"time_offset={self.time_offset}")
        parts.append(f"noise_mask_method={self.noise_mask_method.value}")
        if self.wind_options is not None:
            parts.append(f"azimuth_offset={self.wind_options.azimuth_offset_deg}")
        return ", ".join(parts)


def fetch_calibration(
    session: requests.Session,
    instrument: Instrument,
    date: datetime.date,
) -> Calibration:
    """Most recent calibration on or before `date`. A 404 means the instrument
    has none, which is the common case; any other error is a real failure and
    is raised rather than silently defaulted."""
    resp = session.get(
        f"{API_BASE}/calibration",
        params={"instrumentPid": instrument.pid, "date": date.isoformat()},
        timeout=60,
    )
    data: dict[str, Any] = {}
    if resp.status_code != 404:
        resp.raise_for_status()
        data = resp.json().get("data") or {}

    azimuth_offset = data.get("azimuth_offset")
    noise_mask_method = data.get("noise_mask_method")
    return Calibration(
        time_offset=(
            datetime.timedelta(minutes=data["time_offset"])
            if "time_offset" in data
            else None
        ),
        noise_mask_method=(
            doppy.options.NoiseMaskMethod(noise_mask_method)
            if noise_mask_method is not None
            else doppy.options.NoiseMaskMethod.INTENSITY_AND_VELOCITY
        ),
        # A zero offset is a no-op; cloudnet drops it on the same truthiness test.
        wind_options=(
            WindOptions(azimuth_offset_deg=float(azimuth_offset))
            if azimuth_offset
            else None
        ),
    )


def _offset_window(
    date: datetime.date, time_offset: datetime.timedelta | None
) -> tuple[datetime.date, datetime.date]:
    """Raw-file date range for `date`, widened by one day in the direction the
    calibration offset shifts timestamps, so profiles that cross midnight after
    the shift are still fetched."""
    if time_offset is None:
        return date, date
    if abs(time_offset) >= datetime.timedelta(hours=24):
        raise SystemExit(f"time_offset must be less than 24 hours, got {time_offset}")
    day = datetime.timedelta(days=1)
    if time_offset < datetime.timedelta(0):
        return date - day, date
    if time_offset > datetime.timedelta(0):
        return date, date + day
    return date, date


def _filter_records(
    records: Iterable[RawRec],
    *,
    filename_prefix: str | None = None,
    filename_suffix: str | None = None,
    include_pattern: str | None = None,
    exclude_pattern: str | None = None,
    include_tag_subset: set[str] | None = None,
    exclude_tag_subset: set[str] | None = None,
) -> list[RawRec]:
    inc_re = re.compile(include_pattern, re.I) if include_pattern else None
    exc_re = re.compile(exclude_pattern, re.I) if exclude_pattern else None
    out: list[RawRec] = []
    for r in records:
        if filename_prefix and not r.filename.startswith(filename_prefix):
            continue
        if filename_suffix and not r.filename.endswith(filename_suffix):
            continue
        if inc_re and not inc_re.search(r.filename):
            continue
        if exc_re and exc_re.search(r.filename):
            continue
        if include_tag_subset is not None and not include_tag_subset.issubset(r.tags):
            continue
        if exclude_tag_subset is not None and exclude_tag_subset.issubset(r.tags):
            continue
        out.append(r)
    return out


# ---------------------------------------------------------------- downloading


def download_records(
    session: requests.Session,
    records: list[RawRec],
    target_dir: Path,
) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)

    # doppy parses the original filename (e.g. Background_160324-200018.txt) to
    # extract timestamps, so we keep the name as-is — no uuid prefixes.
    def _one(rec: RawRec) -> tuple[RawRec, Path]:
        dest = target_dir / rec.filename
        if dest.exists() and dest.stat().st_size == rec.size:
            return rec, dest
        tmp = dest.with_suffix(dest.suffix + ".part")
        with session.get(rec.download_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
        tmp.replace(dest)
        return rec, dest

    by_uuid: dict[str, Path] = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(_one, r): r for r in records}
        for fut in as_completed(futs):
            rec, p = fut.result()
            by_uuid[rec.uuid] = p
    return [by_uuid[r.uuid] for r in records]


def _decompress_gz(path: Path) -> Path:
    """Decompress a .gz alongside itself, returning the decompressed path.

    Uses a .part temp file so a corrupt .gz leaves no partial output behind."""
    target = path.with_suffix("")
    if target.exists():
        return target
    tmp = target.with_suffix(target.suffix + ".part")
    with gzip.open(path, "rb") as src, tmp.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    tmp.replace(target)
    return target


def _unzip_gz_files(paths: list[Path]) -> list[Path]:
    return [_decompress_gz(p) if p.suffix == ".gz" else p for p in paths]


# ------------------------------------------------------------ product builders


def _build_stare(
    instrument_id: str,
    co_paths: list[Path],
    cross_paths: list[Path],
    bg_paths: list[Path],
    noise_mask_method: doppy.options.NoiseMaskMethod,
) -> Stare | StareDepol:
    if instrument_id == "halo-doppler-lidar":
        stare = Stare.from_halo_data(
            data=co_paths, data_bg=bg_paths, noise_mask_method=noise_mask_method
        )
        if cross_paths:
            cross = Stare.from_halo_data(
                data=cross_paths,
                data_bg=bg_paths,
                noise_mask_method=noise_mask_method,
            )
            return StareDepol(stare, cross)
        return stare
    if instrument_id in ("wls200s", "wls400s"):
        try:
            return Stare.from_windcube_data(co_paths)
        except ValueError:
            # Some WindCube sites split into multiple "fixed_*" groups; pick
            # the largest with near-vertical zenith — mirrors prod fallback.
            group_re = re.compile(r".+_fixed_(.+)\.nc(?:\..+)?")
            groups: dict[str, list[Path]] = defaultdict(list)
            for p in co_paths:
                if m := group_re.match(p.name):
                    groups[m.group(1)].append(p)
            if not groups:
                raise
            ordered = sorted(groups, key=lambda k: (len(groups[k]), k), reverse=True)
            last_err: Exception | None = None
            for i, key in enumerate(ordered):
                try:
                    candidate = Stare.from_windcube_data(groups[key])
                    zenith = 90 - float(np.median(candidate.elevation))
                    if zenith > ZENITH_ANGLE_THRESHOLD:
                        raise ValueError(f"Invalid zenith angle {zenith}")
                    return candidate
                except (ValueError, doppy.exceptions.NoDataError) as err:
                    last_err = err
                    if i == len(ordered) - 1:
                        raise
            assert last_err is not None
            raise last_err
    raise NotImplementedError(f"stare not implemented for {instrument_id}")


def _build_wind(
    instrument_id: str, paths: list[Path], options: WindOptions | None
) -> Wind:
    if instrument_id == "halo-doppler-lidar":
        return Wind.from_halo_data(data=paths, options=options)
    if instrument_id in ("wls200s", "wls400s"):
        try:
            return Wind.from_windcube_data(data=paths, options=options)
        except ValueError:
            vad_re = re.compile(r".*_vad_(.*)\.nc\.*")
            dbs_re = re.compile(r".*_dbs_(.*)\.nc\.*")
            group_re = vad_re if any(vad_re.match(p.name) for p in paths) else dbs_re
            groups: dict[str, list[Path]] = defaultdict(list)
            for p in paths:
                if m := group_re.match(p.name):
                    groups[m.group(1)].append(p)
            if not groups:
                raise
            biggest = max(groups, key=lambda k: len(groups[k]))
            return Wind.from_windcube_data(data=groups[biggest], options=options)
    if instrument_id in ("wls70", "wls77"):
        return Wind.from_wls70_data(data=paths, options=options)
    raise NotImplementedError(f"wind not implemented for {instrument_id}")


# ------------------------------------------------------- post-processing trims


def _trim_to_date(
    product: Any,
    date: datetime.date,
    time_offset: datetime.timedelta | None = None,
) -> None:
    """Shift timestamps by the calibration offset and drop profiles that fall
    outside the target date, in place.

    Cloudnet does this while writing daily.nc, so a product it publishes never
    contains the neighbouring-day profiles doppy happily returns."""
    n_time = len(product.time)
    if time_offset is not None:
        product.time -= np.timedelta64(time_offset, "us")
    is_valid = product.time.astype("datetime64[D]") == np.datetime64(date)
    if not np.any(is_valid):
        raise SystemExit("No valid timestamps found")
    for field in dataclasses.fields(product):
        value = getattr(product, field.name)
        if isinstance(value, np.ndarray) and value.shape[:1] == (n_time,):
            setattr(product, field.name, value[is_valid])


def _check_zenith_angle(stare: Stare | StareDepol) -> float:
    """Median zenith angle, rejected above 15 degrees as the harmonizer does."""
    zenith = 90 - float(np.median(stare.elevation))
    if zenith > ZENITH_ANGLE_THRESHOLD:
        raise SystemExit(f"Invalid zenith angle {zenith}")
    return zenith


# ------------------------------------------------------------- raw-file parsing


RawParsed = HaloHpl | HaloBg | HaloSysParams | WindCubeFixed | WindCube | Wls70 | Wls77


@dataclass
class RawFileResult:
    rec: RawRec
    path: Path
    kind: str | None  # None => no doppy raw parser matches this file
    parsed: RawParsed | None
    error: Exception | None


def _classify_raw_file(instrument_id: str, filename: str) -> str | None:
    """Raw-parser kind for the file, or None if no doppy parser matches it."""
    if instrument_id == "halo-doppler-lidar":
        if filename.endswith(".hpl"):
            return "HaloHpl"
        if filename.startswith("Background") and filename.endswith(".txt"):
            return "HaloBg"
        if filename.startswith("system_parameters") and filename.endswith(".txt"):
            return "HaloSysParams"
        return None
    if instrument_id in ("wls200s", "wls400s"):
        if not filename.endswith(".nc"):  # .gz already decompressed by caller
            return None
        return "WindCubeFixed" if "fixed" in filename else "WindCube"
    if instrument_id == "wls70" and filename.endswith(".rtd"):
        return "Wls70"
    if instrument_id == "wls77" and filename.endswith(".rtd"):
        return "Wls77"
    return None


def _parse_raw_file(kind: str, path: Path) -> RawParsed:
    """Parse the file at `path` with the parser identified by `kind`."""
    match kind:
        case "HaloHpl":
            return HaloHpl.from_src(path)
        case "HaloBg":
            return HaloBg.from_src(path)
        case "HaloSysParams":
            return HaloSysParams.from_src(path)
        case "WindCubeFixed":
            return WindCubeFixed.from_fixed_src(path)
        case "WindCube":
            return WindCube.from_vad_or_dbs_src(path)
        case "Wls70":
            return Wls70.from_src(path)
        case "Wls77":
            return Wls77.from_src(path)
    raise ValueError(f"Unknown raw parser kind: {kind}")


def _process_raw_file(rec: RawRec, path: Path) -> RawFileResult:
    """Decompress, classify, and parse one downloaded raw file. Never raises;
    a corrupt .gz or unparsable file is captured in the returned result."""
    kind: str | None = None
    try:
        if path.suffix == ".gz":
            path = _decompress_gz(path)
        kind = _classify_raw_file(rec.instrument_id, path.name)
        if kind is None:
            return RawFileResult(rec, path, None, None, None)
        parsed = _parse_raw_file(kind, path)
    except Exception as err:  # corrupt .gz / parse failure — isolate per file
        return RawFileResult(rec, path, kind, None, err)
    return RawFileResult(rec, path, kind, parsed, None)


# ------------------------------------------------------------- orchestration


def _pick_instrument(
    session: requests.Session,
    site: str,
    date: datetime.date,
    product: str,
    override: str | None = None,
    pid_override: str | None = None,
) -> Instrument:
    records = fetch_raw_records(session, site, date, date, instrument=None)
    if not records:
        raise SystemExit(f"No raw uploads for site={site} date={date}")

    if pid_override is not None:
        records = [r for r in records if r.instrument_pid == pid_override]
        if not records:
            raise SystemExit(f"No uploads for PID {pid_override} at {site} {date}")

    available = {r.instrument_id for r in records}
    if override is not None:
        if override not in available:
            raise SystemExit(
                f"Instrument {override!r} has no uploads at {site} {date}. "
                f"Available: {sorted(available)}"
            )
        instrument_id = override
    else:
        candidates = [i for i in PRODUCT_INSTRUMENT_PRIORITY[product] if i in available]
        if not candidates:
            raise SystemExit(
                f"No instruments for product {product!r} at {site} {date}. "
                f"Available: {sorted(available)}"
            )
        instrument_id = candidates[0]

    matching = [r for r in records if r.instrument_id == instrument_id]
    pids = {r.instrument_pid for r in matching}
    if len(pids) > 1:
        raise SystemExit(
            f"{instrument_id} has {len(pids)} units uploading at {site} {date}; "
            "cloudnet processes them separately. Pick one with --instrument-pid:\n"
            + "\n".join(f"  {pid}" for pid in sorted(pids))
        )
    return Instrument(
        id=instrument_id,
        pid=pids.pop(),
        site_altitude=matching[0].site_altitude,
    )


def _fetch_halo_records(
    session: requests.Session,
    site: str,
    date: datetime.date,
    instrument: Instrument,
    time_offset: datetime.timedelta | None,
) -> tuple[list[RawRec], list[RawRec], list[RawRec], list[RawRec]]:
    """Fetch HALO uploads spanning `date` ± 1 day and partition into
    ``(stare_co, stare_cross, wind, bg)``. Stare/wind keep only the days the
    calibration offset can shift onto `date`; bg keeps the full window so the
    background fit has neighbours on both sides."""
    bg_from = date - datetime.timedelta(days=1)
    bg_to = date + datetime.timedelta(days=1)
    all_recs = fetch_raw_records(
        session, site, bg_from, bg_to, instrument.id, instrument.pid
    )

    start, end = _offset_window(date, time_offset)

    def _on_date(recs: list[RawRec]) -> list[RawRec]:
        return [r for r in recs if start <= r.measurement_date <= end]

    stare_co = _on_date(
        _filter_records(
            all_recs,
            filename_prefix="Stare",
            filename_suffix=".hpl",
            exclude_tag_subset={"cross"},
        )
    )
    stare_cross = _on_date(
        _filter_records(
            all_recs,
            filename_prefix="Stare",
            filename_suffix=".hpl",
            include_tag_subset={"cross"},
        )
    )
    wind = _on_date(
        _filter_records(
            all_recs,
            include_pattern=r".*\.hpl",
            exclude_pattern=r"Stare.*",
            exclude_tag_subset={"cross"},
        )
    )
    bg = _filter_records(all_recs, filename_prefix="Background", filename_suffix=".txt")
    return stare_co, stare_cross, wind, bg


def run_stare(
    session: requests.Session,
    site: str,
    date: datetime.date,
    instrument: Instrument,
    calibration: Calibration,
    cache_dir: Path,
) -> Stare | StareDepol:
    if instrument.id == "halo-doppler-lidar":
        co, cross, _, bg = _fetch_halo_records(
            session, site, date, instrument, calibration.time_offset
        )
        if not co:
            raise SystemExit("No co-polarized Stare*.hpl files")
        if not bg:
            raise SystemExit("No Background*.txt files in ±1 day window")
        logging.info(
            "Downloading %d co + %d cross + %d bg files",
            len(co),
            len(cross),
            len(bg),
        )
        co_paths = download_records(session, co, cache_dir / "co")
        cross_paths = download_records(session, cross, cache_dir / "cross")
        bg_paths = download_records(session, bg, cache_dir / "bg")
        stare = _build_stare(
            instrument.id,
            co_paths,
            cross_paths,
            bg_paths,
            calibration.noise_mask_method,
        )
        _trim_to_date(stare, date, calibration.time_offset)
        _check_zenith_angle(stare)
        return stare

    if instrument.id in ("wls200s", "wls400s"):
        recs = fetch_raw_records(
            session, site, date, date, instrument.id, instrument.pid
        )
        fixed = _filter_records(recs, include_pattern=r".*fixed.*\.nc(\..+)?")
        if not fixed:
            raise SystemExit("No WindCube fixed_*.nc(.gz) files")
        logging.info("Downloading %d WindCube fixed files", len(fixed))
        paths = download_records(session, fixed, cache_dir / "fixed")
        paths = _unzip_gz_files(paths)
        stare = _build_stare(
            instrument.id, paths, [], [], calibration.noise_mask_method
        )
        _trim_to_date(stare, date)
        _check_zenith_angle(stare)
        return stare

    raise SystemExit(f"stare not implemented for {instrument.id}")


def run_wind(
    session: requests.Session,
    site: str,
    date: datetime.date,
    instrument: Instrument,
    calibration: Calibration,
    cache_dir: Path,
) -> Wind:
    if instrument.id == "halo-doppler-lidar":
        start, end = _offset_window(date, calibration.time_offset)
        recs = fetch_raw_records(
            session, site, start, end, instrument.id, instrument.pid
        )
        wind_recs = _filter_records(
            recs,
            include_pattern=r".*\.hpl",
            exclude_pattern=r"Stare.*",
            exclude_tag_subset={"cross"},
        )
        if not wind_recs:
            raise SystemExit("No HALO wind .hpl files (non-Stare, non-cross)")
        logging.info("Downloading %d HALO wind files", len(wind_recs))
        paths = download_records(session, wind_recs, cache_dir / "wind")
        wind = _build_wind(instrument.id, paths, calibration.wind_options)
        _trim_to_date(wind, date, calibration.time_offset)
        return wind

    if instrument.id in ("wls200s", "wls400s"):
        recs = fetch_raw_records(
            session, site, date, date, instrument.id, instrument.pid
        )
        wind_recs = _filter_records(recs, include_pattern=r".*(vad)|(dbs).*\.nc.*")
        if not wind_recs:
            raise SystemExit("No WindCube vad/dbs .nc files")
        logging.info("Downloading %d WindCube wind files", len(wind_recs))
        paths = download_records(session, wind_recs, cache_dir / "wind")
        paths = _unzip_gz_files(paths)
        wind = _build_wind(instrument.id, paths, calibration.wind_options)
        _trim_to_date(wind, date)
        return wind

    if instrument.id in ("wls70", "wls77"):
        recs = fetch_raw_records(
            session, site, date, date, instrument.id, instrument.pid
        )
        wind_recs = _filter_records(recs, include_pattern=r".*\.rtd")
        if not wind_recs:
            raise SystemExit("No WLS70 .rtd files")
        logging.info("Downloading %d WLS70 files", len(wind_recs))
        paths = download_records(session, wind_recs, cache_dir / "wind")
        # WLS70 timestamps are pre-trimmed upstream, so cloudnet writes them as-is.
        return _build_wind(instrument.id, paths, calibration.wind_options)

    raise SystemExit(f"wind not implemented for {instrument.id}")


def _pulse_repetition_frequency(los_range: np.ndarray) -> float:
    span = float(los_range.max() - los_range.min())
    round_trip_time = 2 * span / scipy.constants.c
    if round_trip_time < 1 / 15_000:
        return 15e3
    if round_trip_time < 1 / 10_000:  # Halo XR instruments operate slower
        return 10e3
    raise SystemExit(
        f"Suspiciously large range ({span} m). Cannot infer pulse repetition rate"
    )


def _ray_accumulation_time(stare: Stare | StareDepol, los_range: np.ndarray) -> float:
    """Seconds per ray, derived the way cloudnetpy reads it off the
    doppler-lidar product: straight from the file when the instrument reports
    it, otherwise from the pulse count over a frequency inferred from range."""
    match stare.ray_info:
        case RayAccumulationTime(value):
            return float(value)
        case PulsesPerRay(value):
            return float(value) / _pulse_repetition_frequency(los_range)


def _screened_wind_speed(wind: Wind) -> np.ndarray:
    """Horizontal wind speed over the wind grid, with flagged cells filled by
    interpolation.

    cloudnetpy reads uwind/vwind out of the wind product, where the screening
    mask is already applied, and interpolates across the gaps. Passing the
    flagged values through instead would feed failed retrievals — which can
    reach implausible speeds — straight into both turbulent length scales."""
    mask = wind.mask | np.isnan(wind.zonal_wind) | np.isnan(wind.meridional_wind)
    if np.all(mask):
        raise SystemExit("Wind product is entirely masked")
    speed = np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2)
    time = np.broadcast_to(wind.time[:, None], mask.shape)[~mask]
    height = np.broadcast_to(wind.height[None, :], mask.shape)[~mask]
    if len(np.unique(time)) < 3 or len(np.unique(height)) < 3:
        raise SystemExit("Not enough unique wind values for interpolation")

    points = list(zip(time, height, strict=True))
    linear = LinearNDInterpolator(points, speed[~mask])
    nearest = NearestNDInterpolator(points, speed[~mask])
    grid = np.meshgrid(wind.time, wind.height, indexing="ij")
    interpolated = linear(*grid)
    # Linear interpolation leaves NaN outside the convex hull of valid cells.
    outside = np.isnan(interpolated)
    interpolated[outside] = nearest(*grid)[outside]
    if np.isnan(interpolated).any():
        raise SystemExit("Unexpected NaNs in interpolated wind speed")
    return np.asarray(interpolated, dtype=np.float64)


def run_turbulence(
    session: requests.Session,
    site: str,
    date: datetime.date,
    instrument: Instrument,
    calibration: Calibration,
    cache_dir: Path,
) -> Turbulence:
    if instrument.id != "halo-doppler-lidar":
        raise SystemExit(f"turbulence only supported for HALO, not {instrument.id}")

    stare_co, _, wind_recs, bg = _fetch_halo_records(
        session, site, date, instrument, calibration.time_offset
    )

    if not stare_co:
        raise SystemExit("No HALO co-polarized Stare*.hpl files")
    if not wind_recs:
        raise SystemExit("No HALO wind .hpl files (non-Stare, non-cross)")
    if not bg:
        raise SystemExit("No HALO Background*.txt files in ±1 day window")

    logging.info(
        "Downloading %d stare + %d wind + %d bg files",
        len(stare_co),
        len(wind_recs),
        len(bg),
    )
    stare_paths = download_records(session, stare_co, cache_dir / "stare")
    wind_paths = download_records(session, wind_recs, cache_dir / "wind")
    bg_paths = download_records(session, bg, cache_dir / "bg")

    stare = Stare.from_halo_data(
        data=stare_paths,
        data_bg=bg_paths,
        noise_mask_method=calibration.noise_mask_method,
    )
    _trim_to_date(stare, date, calibration.time_offset)
    zenith = _check_zenith_angle(stare)

    wind = _build_wind(instrument.id, wind_paths, calibration.wind_options)
    _trim_to_date(wind, date, calibration.time_offset)

    # cloudnet derives epsilon from the two harmonized products rather than from
    # raw files, so the inputs carry that file's conventions: heights above mean
    # sea level, and a range along the line of sight instead of above the
    # instrument. Both feed the length scales, so reproduce them here.
    los_range = stare.radial_distance / np.cos(np.radians(zenith))
    options = TurbOptions(
        ray_accumulation_time=_ray_accumulation_time(stare, los_range),
        period=EPSILON_WINDOW_SECONDS,
    )
    logging.info(
        "Epsilon options: ray_accumulation_time=%.3f s, period=%.0f s",
        options.ray_accumulation_time,
        options.period,
    )
    return Turbulence.from_winds(
        VerticalWind(
            time=stare.time,
            height=stare.radial_distance + instrument.site_altitude,
            w=stare.radial_velocity,
            mask=stare.mask_radial_velocity,
        ),
        HorizontalWind(
            time=wind.time,
            height=wind.height + instrument.site_altitude,
            V=_screened_wind_speed(wind),
        ),
        options,
    )


def run_raw(
    session: requests.Session,
    site: str,
    date: datetime.date,
    instrument: Instrument,
    cache_dir: Path,
) -> list[RawFileResult]:
    recs = fetch_raw_records(session, site, date, date, instrument.id, instrument.pid)
    if not recs:
        raise SystemExit(f"No raw uploads for {instrument.id} at {site} {date}")

    logging.info("Downloading %d raw files for %s", len(recs), instrument.id)
    paths = download_records(session, recs, cache_dir / "raw")
    return [_process_raw_file(rec, path) for rec, path in zip(recs, paths)]


# ------------------------------------------------------------------- summaries


def _log_stare(stare: Stare | StareDepol) -> None:
    kind = "StareDepol" if isinstance(stare, StareDepol) else "Stare"
    logging.info(
        "Built %s: time=%d, range=%d, system_id=%s, "
        "masked_beta=%.1f%%, masked_v=%.1f%%",
        kind,
        len(stare.time),
        len(stare.radial_distance),
        stare.system_id,
        100.0 * float(np.mean(stare.mask_beta)),
        100.0 * float(np.mean(stare.mask_radial_velocity)),
    )


def _log_wind(wind: Wind) -> None:
    logging.info(
        "Built Wind: time=%d, height=%d, system_id=%s, masked=%.1f%%",
        len(wind.time),
        len(wind.height),
        wind.system_id,
        100.0 * float(np.mean(wind.mask)),
    )


def _log_turbulence(turb: Turbulence) -> None:
    logging.info(
        "Built Turbulence: time=%d, height=%d, masked=%.1f%%",
        len(turb.time),
        len(turb.height),
        100.0 * float(np.mean(turb.mask)),
    )


# -------------------------------------------------------------------- plotting


def _masked_float(data: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.array(data, dtype=float, copy=True)
    out[mask] = np.nan
    return out


def _concise_time_axis(ax: Axes) -> None:
    """Apply a compact, non-rotated date formatter to the x-axis."""
    import matplotlib.dates as mdates

    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))


def _plot_stare(stare: Stare | StareDepol) -> None:
    import matplotlib.pyplot as plt

    with np.errstate(invalid="ignore", divide="ignore"):
        log_beta = np.log10(_masked_float(stare.beta, stare.mask_beta))
    panels: list[tuple[str, np.ndarray, dict]] = [
        ("log10(beta) [sr^-1 m^-1]", log_beta, dict(cmap="viridis", vmin=-7, vmax=-4)),
        (
            "radial velocity [m/s]",
            _masked_float(stare.radial_velocity, stare.mask_radial_velocity),
            dict(cmap="RdBu_r", vmin=-2, vmax=2),
        ),
    ]
    if isinstance(stare, StareDepol):
        depol_mask = stare.mask_beta | stare.mask_depolarisation
        beta_cross_mask = stare.mask_beta | stare.mask_beta_cross
        with np.errstate(invalid="ignore", divide="ignore"):
            log_beta_cross = np.log10(_masked_float(stare.beta_cross, beta_cross_mask))
        panels.append(
            (
                "depolarisation",
                _masked_float(stare.depolarisation, depol_mask),
                dict(cmap="viridis", vmin=0, vmax=0.5),
            )
        )
        panels.append(
            (
                "log10(beta_cross) [sr^-1 m^-1]",
                log_beta_cross,
                dict(cmap="viridis", vmin=-8, vmax=-5),
            )
        )

    fig, axes = plt.subplots(
        len(panels), 1, sharex=True, figsize=(11, 2.5 * len(panels))
    )
    if len(panels) == 1:
        axes = [axes]
    for ax, (label, data, kw) in zip(axes, panels):
        m = ax.pcolormesh(
            stare.time, stare.radial_distance, data.T, shading="auto", **kw
        )
        fig.colorbar(m, ax=ax, label=label)
        ax.set_ylabel("range [m]")
    axes[-1].set_xlabel("time")
    fig.suptitle(f"Stare — system_id={stare.system_id}")
    _concise_time_axis(axes[-1])
    fig.tight_layout()
    plt.show()


def _plot_wind(wind: Wind) -> None:
    import matplotlib.pyplot as plt

    panels = [
        ("zonal wind u [m/s]", _masked_float(wind.zonal_wind, wind.mask)),
        ("meridional wind v [m/s]", _masked_float(wind.meridional_wind, wind.mask)),
    ]
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(11, 5))
    for ax, (label, data) in zip(axes, panels):
        m = ax.pcolormesh(
            wind.time,
            wind.height,
            data.T,
            shading="auto",
            cmap="RdBu_r",
            vmin=-20,
            vmax=20,
        )
        fig.colorbar(m, ax=ax, label=label)
        ax.set_ylabel("height [m]")
    axes[-1].set_xlabel("time")
    fig.suptitle(f"Wind — system_id={wind.system_id}")
    _concise_time_axis(axes[-1])
    fig.tight_layout()
    plt.show()


def _plot_turbulence(turb: Turbulence) -> None:
    import matplotlib.pyplot as plt

    eps = _masked_float(turb.turbulent_kinetic_energy_dissipation_rate, turb.mask)
    with np.errstate(invalid="ignore", divide="ignore"):
        log_eps = np.log10(eps)
    fig, ax = plt.subplots(1, 1, figsize=(11, 4))
    m = ax.pcolormesh(
        turb.time,
        turb.height,
        log_eps.T,
        shading="auto",
        cmap="viridis",
        vmin=-6,
        vmax=-2,
    )
    fig.colorbar(m, ax=ax, label="log10(epsilon) [m^2 s^-3]")
    ax.set_ylabel("height [m]")
    ax.set_xlabel("time")
    fig.suptitle("Turbulence — dissipation rate of turbulent kinetic energy")
    _concise_time_axis(ax)
    fig.tight_layout()
    plt.show()


# ------------------------------------------------------------------- raw output


def _describe_array(arr: np.ndarray) -> str:
    shape = "x".join(str(d) for d in arr.shape)
    if arr.size == 0:
        return f"empty array, shape=({shape})"
    kind = arr.dtype.kind
    if kind == "M":  # datetime64
        valid = arr[~np.isnat(arr)]
        if valid.size == 0:
            return f"datetime64 [{shape}] all-NaT"
        return f"datetime64 [{shape}] {valid.min()}..{valid.max()} ({valid.size} valid)"
    if kind == "b":  # bool
        return f"bool [{shape}] true={int(np.count_nonzero(arr))}/{arr.size}"
    if kind in ("f", "c"):  # float / complex
        nan_count = int(np.count_nonzero(np.isnan(arr)))
        valid = arr[~np.isnan(arr)]
        if valid.size == 0:
            return f"float [{shape}] all-NaN ({arr.size} values)"
        return (
            f"float [{shape}] min={float(valid.min()):.4g} "
            f"max={float(valid.max()):.4g} mean={float(valid.mean()):.4g} "
            f"nan={100.0 * nan_count / arr.size:.1f}%"
        )
    if kind in ("i", "u"):  # signed / unsigned int
        return (
            f"int [{shape}] min={int(arr.min())} max={int(arr.max())} "
            f"unique={int(np.unique(arr).size)}"
        )
    return f"{arr.dtype} [{shape}]"


def _describe_value(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, np.ndarray):
        return _describe_array(value)
    if isinstance(value, np.datetime64):
        return str(value)
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return repr(value.item())
    return repr(value)


def _describe_raw_object(obj: Any, indent: str = "  ") -> list[str]:
    lines: list[str] = []
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            lines.append(f"{indent}{field.name}:")
            lines.extend(_describe_raw_object(value, indent + "  "))
        else:
            lines.append(f"{indent}{field.name}: {_describe_value(value)}")
    return lines


def _summarize_raw(results: list[RawFileResult]) -> None:
    ok: dict[str, int] = defaultdict(int)
    failed: dict[str, int] = defaultdict(int)
    skipped = 0
    for r in results:
        if r.error is not None:
            failed[r.kind or "?"] += 1
        elif r.kind is None:
            skipped += 1
        else:
            ok[r.kind] += 1
    logging.info(
        "Raw: %d files, %d parsed, %d failed, %d unrecognized",
        len(results),
        sum(ok.values()),
        sum(failed.values()),
        skipped,
    )
    for kind in sorted(set(ok) | set(failed)):
        logging.info("  %s: %d parsed, %d failed", kind, ok[kind], failed[kind])
    for r in results:
        if r.error is not None:
            logging.warning("  FAILED %s: %s", r.rec.filename, r.error)


def _show_raw(results: list[RawFileResult]) -> None:
    for i, r in enumerate(results, start=1):
        header = f"[{i}/{len(results)}] {r.rec.filename}  ({r.rec.instrument_id})"
        print(header)
        print("-" * len(header))
        if r.error is not None:
            print(f"  FAILED: {type(r.error).__name__}: {r.error}")
        elif r.kind is None:
            print("  (no doppy raw parser for this file - skipped)")
        else:
            assert r.parsed is not None
            print(f"  parser: {r.kind}")
            for line in _describe_raw_object(r.parsed):
                print(line)
        print()
    _summarize_raw(results)


# -------------------------------------------------------------------------- CLI


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("product", choices=sorted(PRODUCT_INSTRUMENT_PRIORITY))
    parser.add_argument("site", help="Cloudnet site id, e.g. bucharest")
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument(
        "--instrument",
        help="Instrument id to use instead of the auto-picked one",
    )
    parser.add_argument(
        "--instrument-pid",
        help="Instrument PID, when a site has more than one unit of a model",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show quick-look plot; for 'raw', print per-file summaries",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    date = datetime.date.fromisoformat(args.date)
    session = requests.Session()
    instrument = _pick_instrument(
        session,
        args.site,
        date,
        args.product,
        override=args.instrument,
        pid_override=args.instrument_pid,
    )
    logging.info("Using instrument: %s (%s)", instrument.id, instrument.pid)
    calibration = fetch_calibration(session, instrument, date)
    logging.info("Calibration: %s", calibration.describe())
    # Keyed on the PID as well as the id: the id only names the model, so two
    # units at one site would otherwise share a cache directory.
    cache_dir = (
        CACHE_ROOT
        / args.site
        / args.date
        / instrument.id
        / instrument.pid.rsplit("/", 1)[-1]
    )

    match args.product:
        case "stare":
            stare = run_stare(
                session, args.site, date, instrument, calibration, cache_dir
            )
            _log_stare(stare)
            if args.show:
                _plot_stare(stare)
        case "wind":
            wind = run_wind(
                session, args.site, date, instrument, calibration, cache_dir
            )
            _log_wind(wind)
            if args.show:
                _plot_wind(wind)
        case "turbulence":
            turb = run_turbulence(
                session, args.site, date, instrument, calibration, cache_dir
            )
            _log_turbulence(turb)
            if args.show:
                _plot_turbulence(turb)
        case "raw":
            results = run_raw(session, args.site, date, instrument, cache_dir)
            if args.show:
                _show_raw(results)
            else:
                _summarize_raw(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
