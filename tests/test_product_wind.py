import os
import re

import pytest
from doppy import product
from doppy.data.api import Api
from doppy.exceptions import NoDataError

CACHE = "GITHUB_ACTIONS" not in os.environ


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("lindenberg", "2024-02-08", ""),
        ("warsaw", "2023-11-02", "unexpected scan time difference"),
        ("lindenberg", "2023-12-13", "handle header merge"),
        ("neumayer", "2024-01-30", "handle header merge"),
        ("mindelo", "2023-10-23", "unexpected scan time difference"),
        ("hyytiala", "2023-12-13", "unexpected scan time difference"),
        ("warsaw", "2023-06-15", "header merge"),
        ("warsaw", "2023-06-19", "header merge"),
        ("neumayer", "2024-01-16", "header merge"),
        ("hyytiala", "2024-01-01", "ignore scans with small elevation angle"),
    ],
)
def test_wind(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and not rec["filename"].startswith("Stare")
        and "cross" not in set(rec["tags"])
    ]
    _wind = product.Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("lindenberg", "2024-02-08", ""),
    ],
)
def test_wind_with_options(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and not rec["filename"].startswith("Stare")
        and "cross" not in set(rec["tags"])
    ]
    _wind = product.Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        options=product.wind.Options(azimuth_offset_deg=30),
    )


@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("palaiseau", "2024-05-01", "newer file format"),
        ("palaiseau", "2012-01-01", "older file format"),
    ],
)
def test_wind_wls70(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records_wls70 = [
        rec
        for rec in records
        if rec["instrumentId"] == "wls70" and rec["filename"].endswith(".rtd")
    ]
    _wind = product.Wind.from_wls70_data(
        data=[api.get_record_content(r) for r in records_wls70],
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,err,reason",
    [
        ("potenza", "2023-12-06", NoDataError, "max() arg is an empty sequence"),
        ("kenttarova", "2023-03-01", NoDataError, "only scans with elevation angle 0"),
    ],
)
def test_bad_wind(site, date, err, reason):
    api = Api(cache=True)
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and not rec["filename"].startswith("Stare")
        and "cross" not in set(rec["tags"])
    ]
    with pytest.raises(err):
        _wind = product.Wind.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
        )


@pytest.mark.parametrize(
    "site,date,ftype,reason",
    [
        ("payerne", "2024-01-01", "vad", ""),
    ],
)
def test_windcube_wind(site, date, ftype, reason, cache):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    r = re.compile(rf".*{ftype}.*\.nc\..*")
    files = []
    for rec in [rec for rec in records if r.match(rec["filename"])]:
        files.append(api.get_record_content(rec))

    _wind = product.Wind.from_windcube_data(files)


# @pytest.mark.slow
def test_halo_system_id():
    api = Api(cache=CACHE)
    records = api.get_raw_records("lindenberg", "2024-02-08")
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and not rec["filename"].startswith("Stare")
        and "cross" not in set(rec["tags"])
    ]
    wind = product.Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
    )
    assert wind.system_id == "44"


# @pytest.mark.slow
def test_windcube_system_id():
    api = Api(cache=CACHE)
    records = api.get_raw_records("payerne", "2024-01-01")
    r = re.compile(r".*vad.*\.nc\..*")
    files = []
    for rec in [rec for rec in records if r.match(rec["filename"])]:
        files.append(api.get_record_content(rec))

    wind = product.Wind.from_windcube_data(files)
    assert wind.system_id == "WLS200s-197"


# @pytest.mark.slow
def test_wls70_system_id():
    api = Api(cache=CACHE)
    records = api.get_raw_records("palaiseau", "2024-05-01")
    records_wls70 = [
        rec
        for rec in records
        if rec["instrumentId"] == "wls70" and rec["filename"].endswith(".rtd")
    ]
    wind = product.Wind.from_wls70_data(
        data=[api.get_record_content(r) for r in records_wls70],
    )
    assert wind.system_id == "WLS70-10"
