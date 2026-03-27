"""Benchmark helper: runs stare processing and reports timing.

Usage: python -m tests.helpers.bench_helper '<json>'

Input JSON: { "product": "stare", "site": "...", "date": "...",
              "instrument_id": "...", "instrument_uuid": "...",
              "records": [{"filename": "...", "uuid": "...", "path": "...",
                           "instrument_id": "...", "tags": [...]}] }
Output JSON: { "elapsed_secs": 1.234 }
"""

import io
import json
import re
import sys
import time
from collections import defaultdict

from doppy import options, product
from tests.helpers.lock_helper import halo_bg_records, halo_hpl_records


def _load_files(records: list[dict]) -> dict[str, bytes]:
    loaded: dict[str, bytes] = {}
    for r in records:
        with open(r["path"], "rb") as f:
            loaded[r["uuid"]] = f.read()
    return loaded


def bench_stare(case: dict) -> dict:
    records = case["records"]
    instrument_id = case["instrument_id"]

    if instrument_id == "halo-doppler-lidar":
        records_hpl = halo_hpl_records(records)
        records_bg = halo_bg_records(records)
        loaded = _load_files(records_hpl + records_bg)

        data_hpl = [io.BytesIO(loaded[r["uuid"]]) for r in records_hpl]
        data_bg = [(io.BytesIO(loaded[r["uuid"]]), r["filename"]) for r in records_bg]

        start = time.perf_counter()
        product.Stare.from_halo_data(
            data=data_hpl,
            data_bg=data_bg,
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )
        elapsed = time.perf_counter() - start

    elif instrument_id in ("wls100s", "wls200s", "wls400s"):
        r_fixed = re.compile(r".*fixed.*", re.IGNORECASE)
        records_fixed = [r for r in records if r_fixed.match(r["filename"])]
        loaded = _load_files(records_fixed)

        group_pattern = re.compile(r".+_fixed_(.+)\.nc(?:\..+)?")
        group_bufs: dict[str, list] = defaultdict(list)
        for rec in records_fixed:
            if match := group_pattern.match(rec["filename"]):
                group_bufs[match.group(1)].append(io.BytesIO(loaded[rec["uuid"]]))

        start = time.perf_counter()
        for bufs in group_bufs.values():
            product.Stare.from_windcube_data(data=bufs)
            break
        elapsed = time.perf_counter() - start

    else:
        raise ValueError(f"Unsupported instrument for stare: {instrument_id!r}")

    return {"elapsed_secs": elapsed}


BENCHMARKS = {"stare": bench_stare}


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python -m tests.helpers.bench_helper '<json>'",
            file=sys.stderr,
        )
        sys.exit(1)

    case = json.loads(sys.argv[1])
    product_type = case["product"]
    bench = BENCHMARKS.get(product_type)
    if bench is None:
        print(json.dumps({"error": f"Unknown product: {product_type}"}))
        sys.exit(1)

    result = bench(case)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
