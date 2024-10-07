import re
from collections import defaultdict

import doppy
import pytest
from doppy.data.api import Api


@pytest.mark.parametrize(
    "site,date,ftype,reason",
    [
        ("payerne", "2024-02-02", "dbs", ""),
        ("payerne", "2024-01-01", "ppi", ""),
        ("payerne", "2024-01-01", "vad", ""),
        ("payerne", "2024-01-01", "fixed", ""),
    ],
)
def test_windcube(site, date, ftype, reason, cache):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    r = re.compile(rf".*{ftype}_(.+)\.nc\..*")
    groups = defaultdict(list)
    for rec in records:
        match_ = r.match(rec["filename"])
        if match_ is None:
            continue
        group = match_.group(1)
        match ftype:
            case "vad" | "dbs":
                try:
                    file = api.get_record_content(rec)
                    raw = doppy.raw.WindCube.from_vad_or_dbs_src(file)
                    groups[group].append(raw)
                except EOFError:
                    continue
            case _:
                return
                raise NotImplementedError
    for group, raws in groups.items():
        raw = doppy.raw.WindCube.merge(raws)
        assert len(raw.time) > 0


@pytest.mark.parametrize(
    "site,date,ftype,reason,err",
    [
        ("payerne", "2024-01-01", "dbs", "", EOFError),
    ],
)
def test_bad_windcube(site, date, ftype, reason, cache, err):
    api = Api(cache=cache)
    records = api.get_raw_records(site, date)
    r = re.compile(rf".*{ftype}.*\.nc\..*")
    raws = []
    with pytest.raises(err):
        for rec in [rec for rec in records if r.match(rec["filename"])]:
            file = api.get_record_content(rec)
            match ftype:
                case "vad" | "dbs":
                    raw = doppy.raw.WindCube.from_vad_or_dbs_src(file)
                    raws.append(raw)
                case _:
                    return
                    raise NotImplementedError
        _raw = doppy.raw.WindCube.merge(raws)
