import doppy
import pytest
from doppydata.api import Api


@pytest.mark.parametrize(
    "site,date,fname,uuid,reason,len_time",
    [
        (
            "warsaw",
            "2023-12-30",
            "system_parameters_213_202312.txt",
            "fc6a3359-75f3-4625-b0e4-4f404e1d6c5d",
            "File with 12H timestamp",
            22227,
        ),
        (
            "potenza",
            "2023-11-27",
            "system_parameters_194_202311.txt",
            "dcf5bb20-6ae8-43c7-8937-6a83cebf44be",
            "File with 24H timestamp",
            20873,
        ),
        (
            "granada",
            "2023-02-01",
            "system_parameters_258_202302.txt",
            "ef32a9a1-30ec-4142-b805-994f287132f7",
            "File with 12H and 24H timestamp",
            19450,
        ),
        (
            "potenza",
            "2023-12-27",
            "system_parameters_194_202312.txt",
            "f50243e4-63f9-42eb-8e9f-70006c892ddc",
            "File with decimal , and .",
            20019,
        ),
        (
            "granada",
            "2023-07-01",
            "system_parameters_258_202307.txt",
            "4eeb4a8c-8e58-4124-9b3e-57e949afaf63",
            "File null chars",
            6,
        ),
    ],
)
def test_good_system_parameters_files(site, date, fname, uuid, reason, len_time):
    api = Api()
    records = api.get(
        "raw-files",
        {
            "site": site,
            "instrument": "halo-doppler-lidar",
            "filename": fname,
            "date": date,
        },
    )
    assert len(records) == 1
    record = records[0]
    assert record["uuid"] == uuid
    sp = doppy.raw.HaloSysParams.from_src(api.get_record_content(record))
    assert len(sp.time) == len_time
