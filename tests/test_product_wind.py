import pytest
from doppy import options, product
from doppy.data.api import Api


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("lindenberg", "2024-02-08", ""),
    ],
)
def test_wind(site, date, reason):
    api = Api(cache=True)
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
