import os

from doppy import product
from doppy.data.api import Api

CACHE = "GITHUB_ACTIONS" not in os.environ


def plot_winds(site, date):
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


def main():
    for site, date in [("lindenberg", "2024-01-01")]:
        plot_winds(site, date)


if __name__ == "__main__":
    main()
