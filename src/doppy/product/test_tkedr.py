import pathlib
import pickle

from doppy.data.api import Api
from doppy.options import BgCorrectionMethod
from doppy.product.stare import Stare
from doppy.product.tkedr import Tkedr
from doppy.product.wind import Wind


def test(site, date):
    stare, wind = _get_stare_and_wind(site, date)
    pulses_per_ray = 10_000
    pulse_repetition_rate = 15e3  # 1/s
    integration_time = pulses_per_ray / pulse_repetition_rate
    beam_divergence = 33e-6  # radians
    Tkedr.from_stare_and_wind(stare, wind)


def _get_stare_and_wind(site, date):
    path = pathlib.Path("cache", "test_cache.pkl")
    if path.is_file():
        with path.open("rb") as f:
            return pickle.load(f)
    api = Api(cache=True)
    records = api.get_raw_records(site, date)
    records_hpl_stare = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and "cross" not in set(rec["tags"])
        and rec["filename"].startswith("Stare")
    ]
    records_hpl_wind = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and "cross" not in set(rec["tags"])
        and rec["filename"].startswith("VAD")
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_stare],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=BgCorrectionMethod.FIT,
    )
    wind = Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_wind],
    )
    with path.open("wb") as f:
        pickle.dump((stare, wind), f)
    return stare, wind


if __name__ == "__main__":
    site = "warsaw"
    date = "2024-09-21"
    test(site, date)
