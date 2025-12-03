import argparse
from pathlib import Path
from pprint import pprint

import doppy
import numpy as np
from dataset import Dataset, Record
from doppy.exceptions import RawParsingError
from doppy.options import BgCorrectionMethod
from doppy.product import Stare, StareDepol
from doppy.product.turbulence import HorizontalWind, Options, Turbulence, VerticalWind
from doppy.product.wind import Wind


def main():
    args = _parse_args()
    match args.product:
        case "raw":
            _process_raw(args)
        case "stare":
            _process_stare(args)
        case "turbulence":
            _process_turbulence(args)
        case _:
            raise NotImplementedError


def _process_stare(args):
    data = Dataset(site=args.site, date=args.date, instrument_type="Doppler lidar")
    data_hpl = []
    data_hpl_cross = []
    data_bg = []
    for record, path in data.iter():
        if record.filename.startswith("Background"):
            data_bg.append(path)
        elif record.filename.endswith(".hpl") and "cross" not in record.tags:
            data_hpl.append(path)
        elif record.filename.endswith(".hpl") and "cross" in record.tags:
            data_hpl_cross.append(path)
        pprint(record)

    _stare = Stare.from_halo_data(
        data=data_hpl,
        data_bg=data_bg,
        bg_correction_method=BgCorrectionMethod.FIT,
    )
    if data_hpl_cross:
        _stare_depol = StareDepol.from_halo_data(
            co_data=data_hpl,
            co_data_bg=data_bg,
            cross_data=data_hpl_cross,
            cross_data_bg=data_bg,
            bg_correction_method=doppy.options.BgCorrectionMethod.FIT,
            polariser_bleed_through=0,
        )


def _process_turbulence(args):
    data = Dataset(site=args.site, date=args.date, instrument_type="Doppler lidar")
    data_hpl_stare = [
        path
        for rec, path in data.iter()
        if rec.filename.endswith(".hpl")
        and "cross" not in rec.tags
        and rec.filename.startswith("Stare")
    ]
    data_hpl_wind = [
        path
        for rec, path in data.iter()
        if rec.filename.endswith(".hpl")
        and "cross" not in rec.tags
        and not rec.filename.startswith("Stare")
    ]
    data_bg = [
        path
        for rec, path in data.iter()
        if rec.filename.startswith("Background") and rec.filename.endswith(".txt")
    ]
    stare = Stare.from_halo_data(
        data=data_hpl_stare,
        data_bg=data_bg,
        bg_correction_method=BgCorrectionMethod.FIT,
    )
    wind = Wind.from_halo_data(
        data=data_hpl_wind,
    )
    _turb = Turbulence.from_winds(
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
        Options(ray_accumulation_time=1),
    )


def _process_raw(args: argparse.Namespace):
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
    parser.add_argument("product", choices=("raw", "stare", "turbulence"))
    parser.add_argument("site")
    parser.add_argument("date")
    return parser.parse_args()


if __name__ == "__main__":
    main()
