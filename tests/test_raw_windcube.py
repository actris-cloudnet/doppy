import re

import doppy
import pytest
from doppy.data.api import Api


@pytest.mark.parametrize(
    "site,date,ftype,reason",
    [
        ("payerne", "2024-01-01", "dbs", ""),
        ("payerne", "2024-01-01", "ppi", ""),
        ("payerne", "2024-01-01", "vad", ""),
        ("payerne", "2024-01-01", "fixed", ""),
    ],
)
def test_windcube(site, date, ftype, reason, cache):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    r = re.compile(rf".*{ftype}.*\.nc\..*")
    raws = []
    for rec in [rec for rec in records if r.match(rec["filename"])]:
        file = api.get_record_content(rec)
        match ftype:
            case "vad":
                raws.append(doppy.raw.WindCube.from_vad_src(file))
            case _:
                return
                raise NotImplementedError
    _raw = doppy.raw.WindCube.merge(raws)
