import doppy
import pytest
from doppy.data.api import Api


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
    api = Api()
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
            ValueError,
        ),
    ],
)
def test_bad_bg_files(site, date, fname, reason, err):
    api = Api()
    records = api.get_raw_records(site, date)
    records = [rec for rec in records if rec["filename"] == fname or fname is None]
    assert len(records) > 0
    for record in records:
        file = api.get_record_content(record)
        with pytest.raises(err):
            doppy.raw.HaloBg.from_src(file, record["filename"])
