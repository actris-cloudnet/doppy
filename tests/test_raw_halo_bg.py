import os

import doppy
import pytest
from doppy.data.api import Api

CACHE = "GITHUB_ACTIONS" not in os.environ


@pytest.mark.parametrize(
    "site,date,fname,reason",
    [
        ("warsaw", "2022-12-13", "Background_131222-010016.txt", "Normal bg file"),
        (
            "hyytiala",
            "2023-09-22",
            "Background_220923-130016.txt",
            "Bg file without newlines",
        ),
    ],
)
def test_bg_files(site, date, fname, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records = [rec for rec in records if rec["filename"] == fname or fname is None]
    assert len(records) > 0
    for record in records:
        file = api.get_record_content(record)
        doppy.raw.HaloBg.from_src(file, record["filename"])


@pytest.mark.parametrize(
    "site,date,fname,reason,err",
    [
        (
            "hyytiala",
            "2022-12-26",
            "Background_261222-050029.txt",
            "Measurement data in bg file",
            doppy.exceptions.RawParsingError,
        ),
    ],
)
def test_bad_bg_files(site, date, fname, reason, err):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records = [
        rec
        for rec in records
        if rec["filename"].startswith("Background")
        and (rec["filename"] == fname or fname is None)
    ]
    assert len(records) > 0
    for record in records:
        file = api.get_record_content(record)
        with pytest.raises(err):
            doppy.raw.HaloBg.from_src(file, record["filename"])


@pytest.mark.parametrize(
    "site,date,reason",
    [
        (
            "hyytiala",
            "2022-12-26",
            "Measurement data in bg file",
        ),
    ],
)
def test_some_bad_bg_files(site, date, reason):
    api = Api(cache=CACHE)
    records = api.get_raw_records(site, date)
    records = [rec for rec in records if rec["filename"].startswith("Background")]
    assert len(records) > 0
    bgs = doppy.raw.HaloBg.from_srcs(
        [(api.get_record_content(r), r["filename"]) for r in records]
    )
    assert len(bgs) > 0
