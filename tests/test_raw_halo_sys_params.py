import os
from collections import defaultdict

import doppy
import matplotlib.pyplot as plt
import numpy as np
import pytest
from doppy.data.api import Api

CACHE = "GITHUB_ACTIONS" not in os.environ


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
        (
            "chilbolton",
            "2019-01-01",
            "system_parameters_118_201903.txt",
            "87211312-0259-4000-826e-a65a54da945b",
            "Trailing tab chars, zero column, concatenated floats",
            22018,
        ),
    ],
)
def test_good_system_parameters_files(site, date, fname, uuid, reason, len_time):
    api = Api(cache=CACHE)
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


@pytest.mark.slow
def test_all_sys_params():
    api = Api(cache=CACHE)
    records = api.get(
        "raw-files",
        {
            "instrument": "halo-doppler-lidar",
            "filenamePrefix": "system_parameters",
            "filenameSuffix": ".txt",
        },
    )
    groups = defaultdict(list)

    for r in records:
        groups[r["site"]["id"]].append(r)

    for group, group_records in groups.items():
        print(group)
        raws = []
        for record in group_records:
            try:
                raws.append(
                    doppy.raw.HaloSysParams.from_src(api.get_record_content(record))
                )
            except ValueError as err:
                print(err)
        _raw = (
            doppy.raw.HaloSysParams.merge(raws)
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
        )
        # _plot_raw(raw, group)


def _plot_raw(raw: doppy.raw.HaloSysParams, site: str):
    n = 7
    fig, ax = plt.subplots(n, figsize=(15, n * 4))
    fig.suptitle(site)
    ax[0].plot(np.arange(len(raw.time)), raw.time)
    ax[0].set_title("time")

    ax[1].hist(raw.internal_temperature, bins=1000)
    ax[1].set_title("internal_temperature")

    ax[2].hist(raw.internal_relative_humidity, bins=1000)
    ax[2].set_title("internal_relative_humidity")

    ax[3].hist(raw.supply_voltage, bins=1000)
    ax[3].set_title("supply_voltage")

    ax[4].hist(raw.acquisition_card_temperature, bins=1000)
    ax[4].set_title("acquisition_card_temperature")

    ax[5].hist(raw.pitch, bins=1000)
    ax[5].set_title("pitch")

    ax[6].hist(raw.roll, bins=1000)
    ax[6].set_title("roll")
