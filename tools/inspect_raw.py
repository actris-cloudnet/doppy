import re
from argparse import ArgumentParser, Namespace
from collections import defaultdict

import numpy as np
from dataset import Dataset

from doppy.raw import HaloBg, HaloHpl


def main():
    args = _get_args()
    data = Dataset(site=args.site, date=args.date, instrument_type="Doppler lidar")
    group_records(data)


def group_records(data: Dataset):
    recs = data.records
    reg = re.compile(r"([a-zA-Z0-9]*)_.*")
    groups = defaultdict(list)
    for r in recs:
        m = reg.match(r.filename)
        if not m:
            raise ValueError("filename does not match re")
        key = m.group(1)
        groups[key].append(r)

    for key, recs in groups.items():
        print(f"{key}")
        for r in sorted(recs, key=lambda x: x.filename):
            print(f"    {r.filename}")
            match (r.instrument_id, key.lower()):
                case ("halo-doppler-lidar", "background"):
                    raw = HaloBg.from_src(r.as_path())
                    print(_bg_describe(raw))
                case ("halo-doppler-lidar", _) if r.filename.lower().endswith(".hpl"):
                    hpl = HaloHpl.from_src(r.as_path())
                    print(_hpl_describe(hpl))


def _bg_describe(raw: HaloBg) -> str:
    signal = raw.signal
    times = raw.time
    finite_mask = np.isfinite(signal)
    nan_count = int(np.isnan(signal).sum())
    inf_count = int(np.isinf(signal).sum())

    if times.size == 1:
        time_line = f"time: {times[0]}"
    else:
        time_line = f"time: n={times.size}, {times.min()} -> {times.max()}"

    lines = [
        time_line,
        f"signal: shape={signal.shape}, ngates={raw.ngates}",
    ]
    if finite_mask.any():
        finite = signal[finite_mask]
        lines.append(
            f"  min={finite.min():.6g} max={finite.max():.6g} "
            f"median={np.median(finite):.6g} mean={finite.mean():.6g}"
        )
    if nan_count or inf_count:
        lines.append(f"  non-finite: nan={nan_count} inf={inf_count}")

    indent = "        "
    return "\n".join(f"{indent}{ln}" for ln in lines)


def _hpl_describe(raw: HaloHpl) -> str:
    elevations = sorted(raw.elevation_angles)
    lines = [
        f"scan_type: {raw.header.scan_type!r}",
        f"time: shape={raw.time.shape}",
        f"radial_distance: shape={raw.radial_distance.shape}",
        f"radial_velocity: shape={raw.radial_velocity.shape}",
        f"elevation angles: {elevations}",
    ]
    indent = "        "
    return "\n".join(f"{indent}{ln}" for ln in lines)


def _get_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("site", type=str, default="uto", nargs="?")
    parser.add_argument("date", type=str, default="2026-05-18", nargs="?")
    return parser.parse_args()


if __name__ == "__main__":
    main()
