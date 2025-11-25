import os
import pathlib
import re
import tempfile
from collections import defaultdict

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
        ("potenza", "2023-12-06", ""),
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
    wind = product.Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
    )
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=True) as filename:
        wind.write_to_netcdf(pathlib.Path(filename.name))


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
        if rec["instrument"]["instrumentId"] == "wls70"
        and rec["filename"].endswith(".rtd")
    ]
    _wind = product.Wind.from_wls70_data(
        data=[api.get_record_content(r) for r in records_wls70],
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,err,reason",
    [
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


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,ftype,reason",
    [
        ("payerne", "2024-01-01", "vad", ""),
        ("payerne", "2023-06-13", "vad", ""),
        ("payerne", "2022-01-02", "vad", "time_reference in nc time units"),
        ("cabauw", "2024-10-04", "dbs", ""),
    ],
)
def test_windcube_wind(site, date, ftype, reason, cache):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
    ftype_groups = defaultdict(list)
    for rec in [rec for rec in records if ftype_re.match(rec["filename"])]:
        m = ftype_re.match(rec["filename"])
        group = m.group(1)
        file = api.get_record_content(rec)
        ftype_groups[group].append(file)
    for group, files in ftype_groups.items():
        _wind = product.Wind.from_windcube_data(files)


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,ftype,reason",
    [
        (
            "cabauw",
            "2024-10-10",
            "dbs",
            "'63_100m', '65_100m' with different time resolutions",
        ),
    ],
)
def test_windcube_wind_with_different_filetypes(site, date, ftype, reason, cache):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
    files = [
        api.get_record_content(rec)
        for rec in records
        if ftype_re.match(rec["filename"])
    ]

    wind = product.Wind.from_windcube_data(files)
    assert len(wind.time) > 1


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,ftype,err,reason",
    [
        (
            "payerne",
            "2021-07-07",
            "dbs",
            ValueError,
            "groups: '264_50m', '270_100m', '280_100m'",
        ),
    ],
)
def test_bad_windcube_wind_with_different_filetypes(
    site, date, ftype, err, reason, cache
):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    ftype_re = re.compile(rf".*{ftype}_(.*)\.nc(?:\..*)?")
    files = [
        api.get_record_content(rec)
        for rec in records
        if ftype_re.match(rec["filename"])
    ]

    with pytest.raises(err):
        _wind = product.Wind.from_windcube_data(files)


@pytest.mark.slow
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
        if rec["instrument"]["instrumentId"] == "wls70"
        and rec["filename"].endswith(".rtd")
    ]
    wind = product.Wind.from_wls70_data(
        data=[api.get_record_content(r) for r in records_wls70],
    )
    assert wind.system_id == "WLS70-10"
