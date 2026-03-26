"""Lock helper: runs processing for a test case and outputs stats as JSON.

Usage: python -m tests.helpers.lock_helper '<test-case-json>'

Input (CLI arg): JSON with test case definition including "product" field
    and "records" array with local file paths.
Output (stdout): JSON with { "input": { "files": [...] }, "expect": { ... } }
"""

import hashlib
import io
import json
import re
import sys
from collections import defaultdict

import numpy as np
from scipy import stats as scipy_stats

import doppy
from doppy import options, product
from doppy.product.turbulence import (
    HorizontalWind,
    Turbulence,
    VerticalWind,
)
from doppy.product.turbulence import Options as TurbulenceOptions
from doppy.product.wind import Wind

# ── Stats helpers ────────────────────────────────────────────────────


def _sanitize(v: float) -> float:
    if np.isnan(v) or np.isinf(v):
        return 0.0
    return float(v)


def array_stats(arr: np.ndarray) -> dict:
    flat = arr.flatten().astype(float)
    flat = flat[~np.isnan(flat)]
    if len(flat) == 0:
        return {"mean": 0.0, "var": 0.0, "skew": 0.0, "count": 0}
    return {
        "mean": _sanitize(np.mean(flat)),
        "var": _sanitize(np.var(flat)),
        "skew": _sanitize(scipy_stats.skew(flat)),
        "count": int(len(flat)),
    }


def file_entry(rec: dict, content: bytes) -> dict:
    return {
        "filename": rec["filename"],
        "uuid": rec.get("uuid", ""),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def load_and_track(rec: dict) -> tuple[io.BytesIO, dict]:
    """Load a cached file and return (BytesIO for processing, file_entry for lock)."""
    with open(rec["path"], "rb") as f:
        content = f.read()
    entry = file_entry(rec, content)
    return io.BytesIO(content), entry


# ── Record filters ──────────────────────────────────────────────────


def halo_hpl_records(records: list[dict]) -> list[dict]:
    """Non-cross-polarized HALO HPL records (includes Stare and other modes)."""
    return [
        r
        for r in records
        if r["filename"].endswith(".hpl") and "cross" not in set(r.get("tags", []))
    ]


def halo_wind_records(records: list[dict]) -> list[dict]:
    """Non-cross-polarized, non-Stare HALO HPL records (wind scan modes)."""
    return [
        r
        for r in records
        if r["filename"].endswith(".hpl")
        and not r["filename"].startswith("Stare")
        and "cross" not in set(r.get("tags", []))
    ]


def halo_bg_records(records: list[dict]) -> list[dict]:
    """HALO Background records."""
    return [r for r in records if r["filename"].startswith("Background")]


def halo_cross_records(records: list[dict]) -> list[dict]:
    """Cross-polarized HALO HPL records."""
    return [
        r
        for r in records
        if r["filename"].endswith(".hpl") and "cross" in set(r.get("tags", []))
    ]


# ── Product processors ───────────────────────────────────────────────


def lock_stare(case: dict) -> dict:
    records = case["records"]
    if not records:
        raise RuntimeError(
            f"No records found for site={case['site']!r} date={case['date']!r}"
        )
    files = []
    instrument_id = records[0]["instrument_id"]

    if instrument_id == "halo-doppler-lidar":
        records_hpl = halo_hpl_records(records)
        records_bg = halo_bg_records(records)

        data_hpl = []
        for r in records_hpl:
            buf, entry = load_and_track(r)
            files.append(entry)
            data_hpl.append(buf)

        data_bg = []
        for r in records_bg:
            buf, entry = load_and_track(r)
            files.append(entry)
            data_bg.append((buf, r["filename"]))

        stare = product.Stare.from_halo_data(
            data=data_hpl,
            data_bg=data_bg,
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )
    elif instrument_id in ("wls100s", "wls200s", "wls400s"):
        r_fixed = re.compile(r".*fixed.*", re.IGNORECASE)
        records_fixed = [rec for rec in records if r_fixed.match(rec["filename"])]
        group_pattern = re.compile(r".+_fixed_(.+)\.nc(?:\..+)?")
        group_bufs: dict[str, list] = defaultdict(list)
        for rec in records_fixed:
            if match := group_pattern.match(rec["filename"]):
                group = match.group(1)
                buf, entry = load_and_track(rec)
                files.append(entry)
                group_bufs[group].append(buf)

        # Use first group for stats
        stare = None
        for group, bufs in group_bufs.items():
            stare = product.Stare.from_windcube_data(data=bufs)
            break
        if stare is None:
            raise RuntimeError("No windcube fixed groups found")
    else:
        raise ValueError(f"Unsupported instrument for stare: {instrument_id!r}")

    expect = {
        "time_len": len(stare.time),
        "range_len": len(stare.radial_distance),
        "radial_velocity": array_stats(stare.radial_velocity),
        "beta": array_stats(stare.beta),
        "snr": array_stats(stare.snr),
        "system_id": stare.system_id,
    }
    return {"input": {"files": files}, "expect": expect}


def lock_wind(case: dict) -> dict:
    records = case["records"]
    if not records:
        raise RuntimeError(
            f"No records found for site={case['site']!r} date={case['date']!r}"
        )
    files = []
    instrument_id = records[0]["instrument_id"]

    if instrument_id == "halo-doppler-lidar":
        records_hpl = halo_wind_records(records)

        data_hpl = []
        for r in records_hpl:
            buf, entry = load_and_track(r)
            files.append(entry)
            data_hpl.append(buf)

        opts = case.get("options")
        wind_options = None
        if opts and opts.get("azimuth_offset_deg") is not None:
            wind_options = product.wind.Options(
                azimuth_offset_deg=opts["azimuth_offset_deg"]
            )
        wind = Wind.from_halo_data(data=data_hpl, options=wind_options)

    elif instrument_id == "wls70":
        records_wls70 = [rec for rec in records if rec["filename"].endswith(".rtd")]
        data = []
        for r in records_wls70:
            buf, entry = load_and_track(r)
            files.append(entry)
            data.append(buf)
        wind = Wind.from_wls70_data(data=data)

    elif instrument_id in ("wls100s", "wls200s", "wls400s"):
        ftype = case.get("ftype")
        if ftype:
            ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
            matched = [rec for rec in records if ftype_re.match(rec["filename"])]
        else:
            vad_re = re.compile(r".*vad_(.*)\.nc(?:\..*)?")
            matched = [rec for rec in records if vad_re.match(rec["filename"])]
            if not matched:
                dbs_re = re.compile(r".*dbs_(.*)\.nc(?:\..*)?")
                matched = [rec for rec in records if dbs_re.match(rec["filename"])]
        data = []
        for rec in matched:
            buf, entry = load_and_track(rec)
            files.append(entry)
            data.append(buf)
        wind = Wind.from_windcube_data(data)

    else:
        raise ValueError(f"Unsupported instrument for wind: {instrument_id!r}")

    expect = {
        "time_len": len(wind.time),
        "height_len": len(wind.height),
        "zonal_wind": array_stats(wind.zonal_wind),
        "meridional_wind": array_stats(wind.meridional_wind),
        "vertical_wind": array_stats(wind.vertical_wind),
        "system_id": wind.system_id,
    }
    return {"input": {"files": files}, "expect": expect}


def lock_stare_depol(case: dict) -> dict:
    files = []
    records = case["records"]
    records_hpl_co = halo_hpl_records(records)
    records_bg = halo_bg_records(records)
    records_hpl_cross = halo_cross_records(records)

    co_data = []
    for r in records_hpl_co:
        buf, entry = load_and_track(r)
        files.append(entry)
        co_data.append(buf)

    co_data_bg = []
    bg_raw_bytes = []
    for r in records_bg:
        buf, entry = load_and_track(r)
        files.append(entry)
        bg_raw_bytes.append((buf.getvalue(), r["filename"]))
        co_data_bg.append((buf, r["filename"]))

    cross_data = []
    for r in records_hpl_cross:
        buf, entry = load_and_track(r)
        files.append(entry)
        cross_data.append(buf)

    # Reuse already-downloaded bg data with fresh BytesIO handles
    cross_data_bg = [(io.BytesIO(raw), fn) for raw, fn in bg_raw_bytes]

    sd = product.StareDepol.from_halo_data(
        co_data=co_data,
        co_data_bg=co_data_bg,
        cross_data=cross_data,
        cross_data_bg=cross_data_bg,
        bg_correction_method=options.BgCorrectionMethod.FIT,
        polariser_bleed_through=0,
    )

    expect = {
        "time_len": len(sd.time),
        "range_len": len(sd.radial_distance),
        "beta": array_stats(sd.beta),
        "beta_cross": array_stats(sd.beta_cross),
        "depolarisation": array_stats(sd.depolarisation),
        "system_id": sd.system_id,
    }
    return {"input": {"files": files}, "expect": expect}


def lock_turbulence(case: dict) -> dict:
    files = []
    records = case["records"]
    instrument_id = case.get("instrument_id", "halo-doppler-lidar")

    if instrument_id == "halo-doppler-lidar":
        records_hpl_stare = [
            r for r in halo_hpl_records(records) if r["filename"].startswith("Stare")
        ]
        records_hpl_wind = halo_wind_records(records)
        records_bg = halo_bg_records(records)

        stare_data = []
        for r in records_hpl_stare:
            buf, entry = load_and_track(r)
            files.append(entry)
            stare_data.append(buf)

        bg_data = []
        for r in records_bg:
            buf, entry = load_and_track(r)
            files.append(entry)
            bg_data.append((buf, r["filename"]))

        wind_data = []
        for r in records_hpl_wind:
            buf, entry = load_and_track(r)
            files.append(entry)
            wind_data.append(buf)

        stare = product.Stare.from_halo_data(
            data=stare_data,
            data_bg=bg_data,
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )
        wind = Wind.from_halo_data(data=wind_data)

    elif instrument_id in ("wls100s", "wls200s", "wls400s"):
        inst_records = [r for r in records if r.get("instrument_id") == instrument_id]

        fixed_re = re.compile(r".*fixed.*\.nc(?:\..+)?")
        fixed_records = [r for r in inst_records if fixed_re.match(r["filename"])]
        group_pattern = re.compile(r".+_fixed_(.+)\.nc(?:\..+)?")
        fixed_groups: dict[str, list] = defaultdict(list)
        for r in fixed_records:
            if match := group_pattern.match(r["filename"]):
                fixed_groups[match.group(1)].append(r)
        groups_by_size = sorted(
            fixed_groups, key=lambda k: len(fixed_groups[k]), reverse=True
        )
        stare = None
        for group in groups_by_size:
            stare_data = []
            group_files: list[dict] = []
            for r in fixed_groups[group]:
                buf, entry = load_and_track(r)
                group_files.append(entry)
                stare_data.append(buf)
            try:
                stare = product.Stare.from_windcube_data(data=stare_data)
                files.extend(group_files)
                break
            except (ValueError, doppy.exceptions.NoDataError):
                if group == groups_by_size[-1]:
                    raise
        assert stare is not None

        vad_re = re.compile(r".*vad_(.*)\.nc(?:\..*)?")
        wind_records = [r for r in inst_records if vad_re.match(r["filename"])]
        if not wind_records:
            dbs_re = re.compile(r".*dbs_(.*)\.nc(?:\..*)?")
            wind_records = [r for r in inst_records if dbs_re.match(r["filename"])]
        wind_data = []
        for r in wind_records:
            buf, entry = load_and_track(r)
            files.append(entry)
            wind_data.append(buf)
        wind = Wind.from_windcube_data(wind_data)

    else:
        raise ValueError(f"Unsupported instrument for turbulence: {instrument_id!r}")

    turb = Turbulence.from_winds(
        VerticalWind(
            time=stare.time,
            height=stare.radial_distance,
            w=stare.radial_velocity,
            mask=stare.mask_radial_velocity,
        ),
        HorizontalWind(
            time=wind.time,
            height=wind.height,
            V=np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2),
        ),
        TurbulenceOptions(ray_accumulation_time=1),
    )

    expect = {
        "time_len": len(turb.time),
        "height_len": len(turb.height),
        "dissipation_rate": array_stats(turb.turbulent_kinetic_energy_dissipation_rate),
    }
    return {"input": {"files": files}, "expect": expect}


def lock_raw(case: dict) -> dict:
    kind = case["kind"]
    records = case["records"]
    files = []

    if kind == "halo_hpl":
        matched = [
            r
            for r in records
            if r["filename"] == case.get("filename") and r["uuid"] == case.get("uuid")
        ]
        assert len(matched) == 1
        buf, entry = load_and_track(matched[0])
        files.append(entry)
        raw = doppy.raw.HaloHpl.from_src(buf)
        expect = {
            "time_len": len(raw.time),
            "n_gates": len(raw.radial_distance),
            "intensity": array_stats(raw.intensity),
            "radial_velocity": array_stats(raw.radial_velocity),
        }

    elif kind == "halo_hpl_merge":
        matched = [
            rec
            for rec in records
            if rec["filename"].startswith(case.get("prefix", ""))
            and rec["filename"].endswith(case.get("suffix", ""))
        ]
        data = []
        for r in matched:
            buf, entry = load_and_track(r)
            files.append(entry)
            data.append(buf)
        raws = doppy.raw.HaloHpl.from_srcs(data)
        merged = doppy.raw.HaloHpl.merge(raws).sorted_by_time()
        expect = {
            "time_len": len(merged.time),
            "n_gates": len(merged.radial_distance),
        }

    elif kind == "halo_bg":
        matched = [rec for rec in records if rec["filename"] == case.get("filename")]
        for r in matched:
            buf, entry = load_and_track(r)
            files.append(entry)
            doppy.raw.HaloBg.from_src(buf, r["filename"])
        expect = {"file_count": len(matched)}

    elif kind == "halo_sys_params":
        assert len(records) == 1
        buf, entry = load_and_track(records[0])
        files.append(entry)
        sp = doppy.raw.HaloSysParams.from_src(buf)
        expect = {"time_len": len(sp.time)}

    elif kind == "windcube":
        ftype = case.get("ftype", "dbs")
        if ftype not in ("vad", "dbs"):
            raise ValueError(f"Unsupported windcube ftype: {ftype}")
        ftype_re = re.compile(rf".*{ftype}_(.+)\.nc(?:\..*)?")
        groups: dict[str, list] = defaultdict(list)
        for rec in records:
            match = ftype_re.match(rec["filename"])
            if match is None:
                continue
            buf, entry = load_and_track(rec)
            files.append(entry)
            try:
                raw = doppy.raw.WindCube.from_vad_or_dbs_src(buf)
                groups[match.group(1)].append(raw)
            except EOFError:
                continue

        total_time = 0
        for raws in groups.values():
            merged = doppy.raw.WindCube.merge(raws)
            total_time += len(merged.time)
        expect = {"total_time_len": total_time, "n_groups": len(groups)}

    else:
        raise ValueError(f"Unknown raw kind: {kind}")

    return {"input": {"files": files}, "expect": expect}


# ── Dispatch ─────────────────────────────────────────────────────────

PROCESSORS = {
    "stare": lock_stare,
    "wind": lock_wind,
    "stare_depol": lock_stare_depol,
    "turbulence": lock_turbulence,
    "raw": lock_raw,
}


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m tests.helpers.lock_helper '<json>'", file=sys.stderr)
        sys.exit(1)

    case = json.loads(sys.argv[1])
    product_type = case["product"]
    processor = PROCESSORS.get(product_type)
    if processor is None:
        print(json.dumps({"error": f"Unknown product: {product_type}"}))
        sys.exit(1)

    result = processor(case)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
