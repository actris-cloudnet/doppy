import gzip
import io

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ApiRequestError(Exception):
    pass


class Api:
    def __init__(self) -> None:
        retries = Retry(total=10, backoff_factor=0.2)
        adapter = HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self.session = session
        self.api_endpoint = "https://cloudnet.fmi.fi/api"

    def get(self, path: str, params: dict[str, str | list[str]]) -> list:
        res = self.session.get(
            f"{self.api_endpoint}/{path}", params=params, timeout=1800
        )
        if res.ok:
            data = res.json()
            if isinstance(data, list):
                return data
            raise ApiRequestError(f"Unexpected response type from api: {type(data)}")
        raise ApiRequestError(f"Api request error: {res.status_code}")

    def get_raw_records(self, site: str, date: str) -> list:
        return self.get(
            "raw-files",
            params={
                "instrument": [
                    "halo-doppler-lidar",
                    "wls100s",
                    "wls200s",
                    "wls400s",
                    "wls70",
                ],
                "site": site,
                "date": date,
            },
        )

    def get_records_by_instrument_uuid(
        self, site: str, instrument_uuid: str, date: str
    ) -> list:
        records = self.get(
            "raw-files",
            params={"site": site, "date": date},
        )
        return [
            rec
            for rec in records
            if rec.get("instrument", {}).get("uuid") == instrument_uuid
        ]

    def get_record_content(self, rec: dict) -> io.BytesIO:
        content = self.session.get(rec["downloadUrl"]).content
        if rec["filename"].endswith(".gz"):
            content = gzip.decompress(content)
        return io.BytesIO(content)

    @staticmethod
    def halo_hpl_records(records: list) -> list:
        """Non-cross-polarized HALO HPL records (includes Stare and other modes)."""
        return [
            rec
            for rec in records
            if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
        ]

    @staticmethod
    def halo_wind_records(records: list) -> list:
        """Non-cross-polarized, non-Stare HALO HPL records (wind scan modes)."""
        return [
            rec
            for rec in records
            if rec["filename"].endswith(".hpl")
            and not rec["filename"].startswith("Stare")
            and "cross" not in set(rec["tags"])
        ]

    @staticmethod
    def halo_bg_records(records: list) -> list:
        """HALO Background records."""
        return [rec for rec in records if rec["filename"].startswith("Background")]

    @staticmethod
    def halo_cross_records(records: list) -> list:
        """Cross-polarized HALO HPL records."""
        return [
            rec
            for rec in records
            if rec["filename"].endswith(".hpl") and "cross" in set(rec["tags"])
        ]
