import os

import doppy
import numpy as np
import pytest
from doppy import exceptions
from doppy.data.api import Api

CACHE = "GITHUB_ACTIONS" not in os.environ


@pytest.mark.parametrize(
    "site,date,fname,uuid,reason,len_intensity",
    [
        (
            "bucharest",
            "2021-02-04",
            "Stare_158_20210204_05.hpl",
            "9d246099-6660-45a8-92cf-4ddcc894f386",
            "incomplete profile/file (lines 8840-8869)",
            8800,
        ),
        (
            "bucharest",
            "2021-02-07",
            "Stare_158_20210207_20.hpl",
            "890e09af-09eb-4217-ac08-ffe98852a860",
            "incomplete profile/line/file (line: 42478, last number is just '-' )",
            42000,
        ),
        (
            "granada",
            "2019-05-23",
            "Stare_102_20190523_05.hpl",
            "02e12e15-fee1-4c41-a97d-255c9fee8293",
            "null characters in file (line 255174)",
            692973,
        ),
        (
            "hyytiala",
            "2022-01-15",
            "Stare_46_20220115_23.hpl",
            "f3af0ede-17d4-4d34-86cc-ee7e62986e1a",
            "no pitch and roll",
            40640,
        ),
        (
            "leipzig",
            "2022-07-17",
            "Stare_91_20220717_19.hpl",
            "e1859930-9278-48f7-a62b-505e09546023",
            "header with 'No. of rays in file' and incomplete profile (line 241229)",
            240250,
        ),
        (
            "potenza",
            "2023-10-15",
            "Stare_194_20231015_07.hpl",
            "fd80e5b4-78fb-4e00-9a0c-34b7806c02e6",
            "header with 'Range of measurement' insteead of Altitude. "
            "Instrument spectral width on header divider line",
            382400,
        ),
        (
            "soverato",
            "2021-06-29",
            "Stare_194_20210629_03.hpl",
            "a6524573-605d-481d-8c8b-e3257b0d5b8f",
            "Spectral Width on data line 2",
            526000,
        ),
        (
            "granada",
            "2023-04-25",
            "User3_258_20230425_025358.hpl",
            "1a8ec409-7a2a-4c7f-9e59-9858d1d00b83",
            "header with 'No. of waypoints in file'",
            508158,
        ),
        (
            "granada",
            "2023-03-18",
            "Stare_258_20230318_09.hpl",
            "d8c21845-38df-4261-916b-6b8d6a69d6c2",
            "Trailing incomplete profile",
            16983,
        ),
        (
            "chilbolton",
            "2024-02-05",
            "Stare_118_20240205_23.hpl",
            "8e0eb3ef-0ad2-4a0f-af23-9376a00bb0fa",
            "Timestamp overflow",
            116800,
        ),
    ],
)
def test_hpl_files(site, date, fname, uuid, reason, len_intensity):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records = [
        rec for rec in records if rec["filename"] == fname and rec["uuid"] == uuid
    ]
    assert len(records) == 1
    file = api.get_record_content(records[0])
    raw = doppy.raw.HaloHpl.from_src(file)

    time_overflow = (np.diff(raw.time.astype(float) * 1e-6 / 3600) < -12).any()

    assert not time_overflow

    assert len_intensity == len(raw.intensity.flatten())


@pytest.mark.parametrize(
    "site,date,fname,uuid,reason, err",
    [
        (
            "warsaw",
            "2021-10-04",
            "Stare_213_20211004_08.hpl",
            "95d17473-a6b4-4c19-b216-73310ba21821",
            "Number of gates changes mid file",
            exceptions.RawParsingError,
        ),
        (
            "bucharest",
            "2019-07-16",
            "Stare_158_20190716_14.hpl",
            "a5023d87-0128-40dc-9f2c-e257e6861e71",
            "Header but no data",
            exceptions.RawParsingError,
        ),
        (
            "hyytiala",
            "2022-12-26",
            "Stare_46_20221226_04.hpl",
            "88780818-bb7b-449a-953c-feff6bba0090",
            "Number of gates changes mid file",
            exceptions.RawParsingError,
        ),
        (
            "hyytiala",
            "2022-12-26",
            "Stare_46_20221226_04.hpl",
            "dc1a6f54-1ed0-4b65-abd6-ebbd90f1679a",
            "No header, incomplete profiles",
            exceptions.RawParsingError,
        ),
    ],
)
def test_bad_hpl_files(site, date, fname, uuid, reason, err):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records = [
        rec for rec in records if rec["filename"] == fname and rec["uuid"] == uuid
    ]
    assert len(records) == 1
    for record in records:
        file = api.get_record_content(record)
        with pytest.raises(err):
            doppy.raw.HaloHpl.from_src(file)


@pytest.mark.parametrize(
    "site,date,prefix,suffix,reason",
    [
        ("warsaw", "2023-11-01", "Stare", ".hpl", "Normal Stare files"),
        (
            "chilbolton",
            "2024-01-27",
            "Stare",
            ".hpl",
            "TODO: Check why last hour is missing",
        ),
    ],
)
def test_merge_halo_hpl_raw(site, date, prefix, suffix, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records = [
        rec
        for rec in records
        if rec["filename"].startswith(prefix) and rec["filename"].endswith(suffix)
    ]
    raws = doppy.raw.HaloHpl.from_srcs([api.get_record_content(r) for r in records])
    _raw = doppy.raw.HaloHpl.merge(raws).sorted_by_time()
