import argparse
import pathlib
import re
import sys
import tempfile
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

import numpy as np

import doppy
from doppy import exceptions, options, product
from doppy.product.turbulence import (
    HorizontalWind,
    Turbulence,
    VerticalWind,
)
from doppy.product.turbulence import Options as TurbulenceOptions
from doppy.product.wind import Wind

from .api import Api

ERROR_MAP: dict[str, type[BaseException]] = {
    "RawParsingError": exceptions.RawParsingError,
    "NoDataError": exceptions.NoDataError,
    "ShapeError": exceptions.ShapeError,
    "EOFError": EOFError,
    "ValueError": ValueError,
}


@dataclass
class TestResult:
    name: str
    status: str  # PASS, FAIL, ERROR
    duration: float
    message: str = ""


# ── Helpers ──────────────────────────────────────────────────────────


def expect_error(case: dict, fn):
    """Call fn, assert it raises the error specified in case['expect_error']."""
    err_cls = ERROR_MAP[case["expect_error"]]
    try:
        fn()
        raise AssertionError(f"Expected {case['expect_error']} but no exception raised")
    except err_cls:
        pass


# ── Raw Handlers ─────────────────────────────────────────────────────


def handle_raw_halo_hpl(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records = [
        r
        for r in records
        if r["filename"] == case["filename"] and r["uuid"] == case["uuid"]
    ]
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    file = api.get_record_content(records[0])
    raw = doppy.raw.HaloHpl.from_src(file)
    time_overflow = (np.diff(raw.time.astype(float) * 1e-6 / 3600) < -12).any()
    assert not time_overflow, "Time overflow detected"
    expected = case["expect"]["len_intensity"]
    actual = len(raw.intensity.flatten())
    assert expected == actual, f"len_intensity: expected {expected}, got {actual}"


def handle_raw_halo_hpl_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records = [
        r
        for r in records
        if r["filename"] == case["filename"] and r["uuid"] == case["uuid"]
    ]
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    file = api.get_record_content(records[0])
    expect_error(case, lambda: doppy.raw.HaloHpl.from_src(file))


def handle_raw_halo_hpl_merge(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records = [
        rec
        for rec in records
        if rec["filename"].startswith(case["prefix"])
        and rec["filename"].endswith(case["suffix"])
    ]
    raws = doppy.raw.HaloHpl.from_srcs([api.get_record_content(r) for r in records])
    doppy.raw.HaloHpl.merge(raws).sorted_by_time()


def handle_raw_halo_bg(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records = [rec for rec in records if rec["filename"] == case["filename"]]
    assert len(records) > 0, f"No records found for {case['filename']}"
    for record in records:
        file = api.get_record_content(record)
        doppy.raw.HaloBg.from_src(file, record["filename"])


def handle_raw_halo_bg_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records = [
        rec
        for rec in records
        if rec["filename"].startswith("Background")
        and rec["filename"] == case["filename"]
    ]
    assert len(records) > 0, f"No records found for {case['filename']}"
    for record in records:
        file = api.get_record_content(record)
        expect_error(
            case, lambda f=file: doppy.raw.HaloBg.from_src(f, record["filename"])
        )


def handle_raw_halo_bg_some_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records = Api.halo_bg_records(records)
    assert len(records) > 0, "No BG records found"
    bgs = doppy.raw.HaloBg.from_srcs(
        [(api.get_record_content(r), r["filename"]) for r in records]
    )
    assert len(bgs) > 0, "Expected at least one parsed BG file"


def handle_raw_halo_sys_params(api: Api, case: dict):
    records = api.get(
        "raw-files",
        {
            "site": case["site"],
            "instrument": "halo-doppler-lidar",
            "filename": case["filename"],
            "date": case["date"],
        },
    )
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    record = records[0]
    assert record["uuid"] == case["uuid"], (
        f"UUID mismatch: expected {case['uuid']}, got {record['uuid']}"
    )
    sp = doppy.raw.HaloSysParams.from_src(api.get_record_content(record))
    expected = case["expect"]["len_time"]
    actual = len(sp.time)
    assert expected == actual, f"len_time: expected {expected}, got {actual}"


def handle_raw_halo_sys_params_all(api: Api, _case: dict):
    records = api.get(
        "raw-files",
        {
            "instrument": "halo-doppler-lidar",
            "filenamePrefix": "system_parameters",
            "filenameSuffix": ".txt",
        },
    )
    groups: dict[str, list] = defaultdict(list)
    for r in records:
        groups[r["site"]["id"]].append(r)
    for _group, group_records in groups.items():
        raws = []
        for record in group_records:
            try:
                raws.append(
                    doppy.raw.HaloSysParams.from_src(api.get_record_content(record))
                )
            except ValueError:
                pass
        (
            doppy.raw.HaloSysParams.merge(raws)
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
        )


def handle_raw_windcube(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    ftype = case["ftype"]
    r = re.compile(rf".*{ftype}_(.+)\.nc(?:\..*)?")
    groups: dict[str, list] = defaultdict(list)
    for rec in records:
        match_ = r.match(rec["filename"])
        if match_ is None:
            continue
        group = match_.group(1)
        if ftype not in ("vad", "dbs"):
            return  # skip non-vad/dbs ftypes
        try:
            file = api.get_record_content(rec)
            raw = doppy.raw.WindCube.from_vad_or_dbs_src(file)
            groups[group].append(raw)
        except EOFError:
            continue
    for group, raws in groups.items():
        raw = doppy.raw.WindCube.merge(raws)
        assert len(raw.time) > 0, f"Group {group}: expected time length > 0"


def handle_raw_windcube_bad(api: Api, case: dict):
    ftype = case["ftype"]
    records = api.get_raw_records(case["site"], case["date"])
    r = re.compile(rf".*{ftype}.*\.nc\..*")
    err_cls = ERROR_MAP[case["expect_error"]]
    raws = []
    try:
        for rec in [rec for rec in records if r.match(rec["filename"])]:
            file = api.get_record_content(rec)
            if ftype in ("vad", "dbs"):
                raw = doppy.raw.WindCube.from_vad_or_dbs_src(file)
                raws.append(raw)
            else:
                return
        doppy.raw.WindCube.merge(raws)
        raise AssertionError(f"Expected {case['expect_error']} but no exception raised")
    except err_cls:
        pass


# ── Product Handlers ─────────────────────────────────────────────────


def handle_product_stare(api: Api, case: dict):
    source = case.get("source", "halo")
    if source == "halo":
        records = api.get_raw_records(case["site"], case["date"])
        records_hpl = Api.halo_hpl_records(records)
        records_bg = Api.halo_bg_records(records)
        product.Stare.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
            data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )
    elif source == "windcube":
        records = api.get_raw_records(case["site"], case["date"])
        r = re.compile(r".*fixed.*", re.IGNORECASE)
        records_fixed = [rec for rec in records if r.match(rec["filename"])]
        groups: dict[str, list] = defaultdict(list)
        group_pattern = re.compile(r".+_fixed_(.+)\.nc(?:\..+)?")
        for rec in records_fixed:
            if match := group_pattern.match(rec["filename"]):
                group = match.group(1)
                groups[group].append(rec)
        for group, records_group in groups.items():
            product.Stare.from_windcube_data(
                data=[api.get_record_content(r) for r in records_group],
            )


def handle_product_stare_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl = Api.halo_hpl_records(records)
    records_bg = Api.halo_bg_records(records)

    def run():
        product.Stare.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
            data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )

    expect_error(case, run)


def handle_product_stare_system_id(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl = Api.halo_hpl_records(records)
    records_bg = Api.halo_bg_records(records)
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )
    expected = case["expect"]["system_id"]
    assert stare.system_id == expected, (
        f"system_id: expected {expected!r}, got {stare.system_id!r}"
    )


def handle_product_stare_netcdf(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl = Api.halo_hpl_records(records)
    records_bg = Api.halo_bg_records(records)
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as f:
        stare.write_to_netcdf(f.name)
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as f:
        stare.write_to_netcdf(pathlib.Path(f.name))


def handle_product_wind(api: Api, case: dict):
    source = case.get("source", "halo")
    if source == "halo":
        records = api.get_raw_records(case["site"], case["date"])
        records_hpl = Api.halo_wind_records(records)
        wind = Wind.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
        )
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as f:
            wind.write_to_netcdf(pathlib.Path(f.name))
    elif source == "wls70":
        records = api.get_raw_records(case["site"], case["date"])
        records_wls70 = [
            rec
            for rec in records
            if rec["instrument"]["instrumentId"] == "wls70"
            and rec["filename"].endswith(".rtd")
        ]
        Wind.from_wls70_data(
            data=[api.get_record_content(r) for r in records_wls70],
        )


def handle_product_wind_with_options(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl = Api.halo_wind_records(records)
    opts = case.get("options", {})
    Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        options=product.wind.Options(
            azimuth_offset_deg=opts.get("azimuth_offset_deg", 0),
        ),
    )


def handle_product_wind_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl = Api.halo_wind_records(records)
    expect_error(
        case,
        lambda: Wind.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
        ),
    )


def handle_product_windcube_wind(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    ftype = case["ftype"]
    ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
    ftype_groups: dict[str, list] = defaultdict(list)
    for rec in [rec for rec in records if ftype_re.match(rec["filename"])]:
        m = ftype_re.match(rec["filename"])
        group = m.group(1)  # type: ignore[union-attr]
        file = api.get_record_content(rec)
        ftype_groups[group].append(file)
    for group, files in ftype_groups.items():
        Wind.from_windcube_data(files)


def handle_product_windcube_wind_mixed(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    ftype = case["ftype"]
    ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
    files = [
        api.get_record_content(rec)
        for rec in records
        if ftype_re.match(rec["filename"])
    ]
    wind = Wind.from_windcube_data(files)
    assert len(wind.time) > 1, f"Expected time length > 1, got {len(wind.time)}"


def handle_product_windcube_wind_mixed_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    ftype = case["ftype"]
    ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
    files = [
        api.get_record_content(rec)
        for rec in records
        if ftype_re.match(rec["filename"])
    ]
    expect_error(case, lambda: Wind.from_windcube_data(files))


def handle_product_wind_system_id(api: Api, case: dict):
    source = case["source"]
    expected_id = case["expect"]["system_id"]
    if source == "halo":
        records = api.get_raw_records(case["site"], case["date"])
        records_hpl = Api.halo_wind_records(records)
        wind = Wind.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
        )
    elif source == "windcube":
        records = api.get_raw_records(case["site"], case["date"])
        r = re.compile(r".*vad.*\.nc\..*")
        files = [
            api.get_record_content(rec) for rec in records if r.match(rec["filename"])
        ]
        wind = Wind.from_windcube_data(files)
    elif source == "wls70":
        records = api.get_raw_records(case["site"], case["date"])
        records_wls70 = [
            rec
            for rec in records
            if rec["instrument"]["instrumentId"] == "wls70"
            and rec["filename"].endswith(".rtd")
        ]
        wind = Wind.from_wls70_data(
            data=[api.get_record_content(r) for r in records_wls70],
        )
    else:
        raise ValueError(f"Unknown source: {source}")
    assert wind.system_id == expected_id, (
        f"system_id: expected {expected_id!r}, got {wind.system_id!r}"
    )


def handle_product_stare_depol(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl_co = Api.halo_hpl_records(records)
    records_bg = Api.halo_bg_records(records)
    records_hpl_cross = Api.halo_cross_records(records)
    stare_depol = product.StareDepol.from_halo_data(
        co_data=[api.get_record_content(r) for r in records_hpl_co],
        co_data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        cross_data=[api.get_record_content(r) for r in records_hpl_cross],
        cross_data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
        polariser_bleed_through=0,
    )
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as f:
        stare_depol.write_to_netcdf(pathlib.Path(f.name))


def handle_product_stare_depol_bad(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl_co = Api.halo_hpl_records(records)
    records_bg = Api.halo_bg_records(records)
    records_hpl_cross = Api.halo_cross_records(records)

    def run():
        product.StareDepol.from_halo_data(
            co_data=[api.get_record_content(r) for r in records_hpl_co],
            co_data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
            cross_data=[api.get_record_content(r) for r in records_hpl_cross],
            cross_data_bg=[
                (api.get_record_content(r), r["filename"]) for r in records_bg
            ],
            bg_correction_method=options.BgCorrectionMethod.FIT,
            polariser_bleed_through=0,
        )

    expect_error(case, run)


def handle_product_turbulence(api: Api, case: dict):
    records = api.get_raw_records(case["site"], case["date"])
    records_hpl_stare = [
        r for r in Api.halo_hpl_records(records) if r["filename"].startswith("Stare")
    ]
    records_hpl_wind = Api.halo_wind_records(records)
    records_bg = Api.halo_bg_records(records)
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_stare],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )
    wind = Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_wind],
    )
    Turbulence.from_winds(
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


# ── Handler dispatch ─────────────────────────────────────────────────

HANDLERS: dict[str, object] = {
    "raw.halo_hpl": handle_raw_halo_hpl,
    "raw.halo_hpl_bad": handle_raw_halo_hpl_bad,
    "raw.halo_hpl_merge": handle_raw_halo_hpl_merge,
    "raw.halo_bg": handle_raw_halo_bg,
    "raw.halo_bg_bad": handle_raw_halo_bg_bad,
    "raw.halo_bg_some_bad": handle_raw_halo_bg_some_bad,
    "raw.halo_sys_params": handle_raw_halo_sys_params,
    "raw.halo_sys_params_all": handle_raw_halo_sys_params_all,
    "raw.windcube": handle_raw_windcube,
    "raw.windcube_bad": handle_raw_windcube_bad,
    "product.stare": handle_product_stare,
    "product.stare_bad": handle_product_stare_bad,
    "product.stare_system_id": handle_product_stare_system_id,
    "product.stare_netcdf": handle_product_stare_netcdf,
    "product.wind": handle_product_wind,
    "product.wind_with_options": handle_product_wind_with_options,
    "product.wind_bad": handle_product_wind_bad,
    "product.windcube_wind": handle_product_windcube_wind,
    "product.windcube_wind_mixed": handle_product_windcube_wind_mixed,
    "product.windcube_wind_mixed_bad": handle_product_windcube_wind_mixed_bad,
    "product.wind_system_id": handle_product_wind_system_id,
    "product.stare_depol": handle_product_stare_depol,
    "product.stare_depol_bad": handle_product_stare_depol_bad,
    "product.turbulence": handle_product_turbulence,
}


# ── CLI and main loop ────────────────────────────────────────────────


def format_test_name(table_name: str, case: dict) -> str:
    parts = [table_name]
    if "site" in case:
        parts.append(case["site"])
    if "date" in case:
        parts.append(case["date"])
    if "filename" in case:
        parts.append(case["filename"])
    if "source" in case:
        parts.append(case["source"])
    if "ftype" in case:
        parts.append(case["ftype"])
    name = "::".join(parts)
    if "id" in case:
        return f"[{case['id']}] {name}"
    return name


def print_result(status: str, name: str, duration: float, message: str = ""):
    colors = {
        "PASS": "\033[32m",
        "FAIL": "\033[31m",
        "SKIP": "\033[33m",
        "ERROR": "\033[31m",
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    suffix = f" - {message}" if message else ""
    print(f"  {color}{status}{reset} {name} ({duration:.1f}s){suffix}")


def print_summary(results: list[TestResult]):
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    errors = sum(1 for r in results if r.status == "ERROR")
    skipped = sum(1 for r in results if r.status == "SKIP")
    total = len(results)
    print(f"\n{'=' * 60}")
    print(
        f"Results: {passed} passed, {failed} failed, "
        f"{errors} errors, {skipped} skipped / {total} total"
    )
    if failed or errors:
        print("\033[31mFAILED\033[0m")
    else:
        print("\033[32mALL PASSED\033[0m")


def parse_args():
    parser = argparse.ArgumentParser(description="Run doppy legacy tests")
    parser.add_argument(
        "--category",
        choices=["raw", "product"],
        help="Run only raw or product tests",
    )
    parser.add_argument(
        "--product",
        help="Filter by product name substring (e.g., 'stare', 'wind')",
    )
    parser.add_argument(
        "--site",
        help="Run tests for a specific site only",
    )
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow tests (excluded by default)",
    )
    parser.add_argument(
        "--source",
        help="Run a specific test type (e.g., 'raw.halo_hpl')",
    )
    parser.add_argument(
        "--id",
        help="Run a specific test by its ID (e.g., 'a3f7z2')",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    toml_path = pathlib.Path(__file__).parent / "tests-legacy.toml"
    with open(toml_path, "rb") as f:
        config = tomllib.load(f)

    # Flatten TOML structure into (table_name, case) pairs
    test_cases: list[tuple[str, dict]] = []
    for category, tests_by_type in config.items():
        for test_type, cases in tests_by_type.items():
            table_name = f"{category}.{test_type}"
            for case in cases:
                test_cases.append((table_name, case))

    # Filter
    filtered: list[tuple[str, dict]] = []
    for table_name, case in test_cases:
        category = table_name.split(".")[0]
        if args.category and category != args.category:
            continue
        if case.get("slow", False) and not args.include_slow:
            continue
        if args.site and case.get("site") != args.site:
            continue
        if args.product and args.product not in table_name:
            continue
        if args.source and table_name != args.source:
            continue
        if args.id and case.get("id") != args.id:
            continue
        filtered.append((table_name, case))

    if not filtered:
        print("No tests matched the given filters.")
        sys.exit(0)

    print(f"Running {len(filtered)} tests...\n")

    api = Api()
    results: list[TestResult] = []

    for table_name, case in filtered:
        name = format_test_name(table_name, case)
        handler = HANDLERS.get(table_name)
        if handler is None:
            msg = f"No handler for {table_name}"
            results.append(TestResult(name, "ERROR", 0.0, msg))
            print_result("ERROR", name, 0.0, msg)
            continue

        t0 = time.monotonic()
        try:
            handler(api, case)  # type: ignore[operator]
            duration = time.monotonic() - t0
            results.append(TestResult(name, "PASS", duration))
            print_result("PASS", name, duration)
        except AssertionError as e:
            duration = time.monotonic() - t0
            results.append(TestResult(name, "FAIL", duration, str(e)))
            print_result("FAIL", name, duration, str(e))
        except Exception as e:
            duration = time.monotonic() - t0
            msg = f"{type(e).__name__}: {e}"
            results.append(TestResult(name, "ERROR", duration, msg))
            print_result("ERROR", name, duration, msg)
            traceback.print_exc()

    print_summary(results)
    sys.exit(0 if all(r.status in ("PASS", "SKIP") for r in results) else 1)


if __name__ == "__main__":
    main()
