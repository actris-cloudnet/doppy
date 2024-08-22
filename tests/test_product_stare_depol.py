import os
import pathlib
import tempfile

import pytest
from doppy import exceptions, options, product
from doppy.data.api import Api

CACHE = "GITHUB_ACTIONS" not in os.environ


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("vehmasmaki", "2021-01-02", ""),
        ("vehmasmaki", "2021-06-30", ""),
    ],
)
def test_stare_depol(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl_co = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg_co = [
        rec
        for rec in records
        if rec["filename"].startswith("Background") and "cross" not in set(rec["tags"])
    ]
    records_hpl_cross = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" in set(rec["tags"])
    ]
    records_bg_cross = [
        rec
        for rec in records
        if rec["filename"].startswith("Background") and "cross" in set(rec["tags"])
    ]
    stare_depol = product.StareDepol.from_halo_data(
        co_data=[api.get_record_content(r) for r in records_hpl_co],
        co_data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg_co],
        cross_data=[api.get_record_content(r) for r in records_hpl_cross],
        cross_data_bg=[
            (api.get_record_content(r), r["filename"]) for r in records_bg_cross
        ],
        bg_correction_method=options.BgCorrectionMethod.FIT,
        polariser_bleed_through=0,
    )

    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as filename:
        stare_depol.write_to_netcdf(pathlib.Path(filename.name))


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,err,reason",
    [
        ("hyytiala", "2022-01-01", exceptions.NoDataError, "bg files missing"),
        ("hyytiala", "2022-05-23", exceptions.NoDataError, "bg files missing"),
        ("kenttarova", "2022-08-26", exceptions.NoDataError, "bg files missing"),
    ],
)
def test_bad_stare_depol(site, date, err, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl_co = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg_co = [
        rec
        for rec in records
        if rec["filename"].startswith("Background") and "cross" not in set(rec["tags"])
    ]
    records_hpl_cross = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" in set(rec["tags"])
    ]
    records_bg_cross = [
        rec
        for rec in records
        if rec["filename"].startswith("Background") and "cross" in set(rec["tags"])
    ]
    with pytest.raises(err):
        _depol = product.StareDepol.from_halo_data(
            co_data=[api.get_record_content(r) for r in records_hpl_co],
            co_data_bg=[
                (api.get_record_content(r), r["filename"]) for r in records_bg_co
            ],
            cross_data=[api.get_record_content(r) for r in records_hpl_cross],
            cross_data_bg=[
                (api.get_record_content(r), r["filename"]) for r in records_bg_cross
            ],
            bg_correction_method=options.BgCorrectionMethod.FIT,
            polariser_bleed_through=0,
        )
