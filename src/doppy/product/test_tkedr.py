import pathlib
import pickle

import numpy as np
from netCDF4 import Dataset, num2date

from doppy.data.api import Api
from doppy.options import BgCorrectionMethod
from doppy.product.model import ModelWind
from doppy.product.stare import Stare
from doppy.product.tkedr import Tkedr
from doppy.product.wind import Wind


def test(site, date):
    api = Api(cache=True)
    model_wind = _get_model(api, site, date)
    stare, wind = _get_stare_and_wind(api, site, date)
    Tkedr.from_stare_and_wind(stare, wind, model_wind)


def _get_model(api, site, date):
    res = api.get("model-files", params={"site": site, "date": date})
    res = [r for r in res if r["modelId"] == "ecmwf"]
    if len(res) != 1:
        raise ValueError("unexpected models")
    content = api.get_record_content(res[0])
    nc = Dataset("inmemory.nc", mode="r", memory=content.read())

    uwind = nc["uwind"]  # Zonal wind
    vwind = nc["vwind"]  # Meridional wind
    height = nc["height"]
    time = nc["time"]
    time_np = num2date(time[:].data, time.units).astype("datetime64[us]")
    if (
        uwind[:].mask != False
        or vwind[:].mask != False
        or height[:].mask != False
        or time[:].mask != False
    ):
        raise ValueError

    h = height[:].data
    h_med = np.median(h, axis=0)
    range_mask = h_med < 20e3  # ignore the gates above 20km

    time_ = time_np
    uwind_ = np.array(uwind[:].data[:, range_mask], dtype=np.float64)
    vwind_ = np.array(vwind[:].data[:, range_mask], dtype=np.float64)
    height_ = np.array(h_med[range_mask], dtype=np.float64)

    return ModelWind(
        time=time_,
        height=height_,
        zonal_wind=uwind_,
        meridional_wind=vwind_,
    )


def _get_stare_and_wind(api, site, date):
    path = pathlib.Path("cache", "test_cache.pkl")
    if path.is_file():
        with path.open("rb") as f:
            return pickle.load(f)
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
