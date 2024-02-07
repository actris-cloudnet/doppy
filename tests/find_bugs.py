import datetime

import doppy
from doppydata.api import Api
import json

API = Api()


def find_bugs():
    for i,d in enumerate(_iter_dates(start=1, end=10000)):
        print(i,d)
        for s in _sites(d):
            print(s)
            try:
                _process_date(s, d)
            except (KeyboardInterrupt, SystemExit):
                return
            except Exception as err:
                error_type = type(err).__name__
                error_msg = str(err).replace('\n', '__NEWLINE__')
                log = {"site": s, "date": str(d), "err_type": error_type, "err_msg": error_msg}
                with open("err.log", "a") as f:
                    f.write(json.dumps(log) + "\n")



def _process_date(site, date):
    records = API.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]

    stare = doppy.product.Stare.from_halo_data(
        data=[API.get_record_content(r) for r in records_hpl],
        data_bg=[(API.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=doppy.options.BgCorrectionMethod.FIT,
    )


def _sites(date):
    records = API.get("raw-files", {"instrument": "halo-doppler-lidar", "date": date})
    return sorted(list(set((r["siteId"] for r in records))))


def _iter_dates(start=0, end=10):
    for i in range(start, end):
        yield (datetime.datetime.now() - datetime.timedelta(days=i)).date()


if __name__ == "__main__":
    find_bugs()
