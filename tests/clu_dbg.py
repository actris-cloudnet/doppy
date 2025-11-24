import argparse
from pathlib import Path

import doppy
from dataset import Dataset, Record
from doppy.exceptions import RawParsingError


def main():
    args = _parse_args()
    data = Dataset(site=args.site, date=args.date, instrument_type="Doppler lidar")
    for record, path in data.iter():
        match (record.filename, record.instrument_id):
            case (fname, "halo-doppler-lidar") if fname.endswith("hpl"):
                _process_halo_hpl(record, path)
            case (fname, "halo-doppler-lidar") if fname.startswith("Background"):
                _process_halo_bg(record, path)
            case _:
                print(record)
                raise NotImplementedError


def _process_halo_bg(rec: Record, path: Path):
    try:
        raw = doppy.raw.HaloBg.from_src(path)
        print(f"""Processed {rec.filename}
              shape: {raw.signal.shape}
              """)
    except RawParsingError as err:
        print(f"""Failed to process {rec.filename}
              err: {err}
              """)


def _process_halo_hpl(rec: Record, path: Path):
    try:
        raw = doppy.raw.HaloHpl.from_src(path)
        nprofiles = len(raw.time)
        ngates = len(raw.radial_distance)
        azimuth_angles = sorted(list({round(a, 1) for a in raw.azimuth}))
        elevation_angles = sorted(list({round(a, 1) for a in raw.elevation}))

        print(f"""Processed {rec.filename}
              nprofiles: {nprofiles}
              ngates: {ngates}
              azimuths: {azimuth_angles}
              elevations: {elevation_angles}
              """)
    except RawParsingError as err:
        print(f"""Failed to process {rec.filename}
              err: {err}
              """)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("site")
    parser.add_argument("date")
    return parser.parse_args()


if __name__ == "__main__":
    main()
