import gzip
import io

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from doppy.data import exceptions
from doppy.data.cache import cached_record


class Api:
    def __init__(self, cache: bool = False) -> None:
        retries = Retry(total=10, backoff_factor=0.2)
        adapter = HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self.session = session
        self.api_endpoint = "https://cloudnet.fmi.fi/api"
        self.cache = cache

    def get(self, path: str, params: dict[str, str]) -> list:
        res = self.session.get(
            f"{self.api_endpoint}/{path}", params=params, timeout=1800
        )
        if res.ok:
            data = res.json()
            if isinstance(data, list):
                return data
            raise exceptions.ApiRequestError(
                f"Unexpected response type from api: {type(data)}"
            )
        raise exceptions.ApiRequestError(f"Api request error: {res.status_code}")

    def get_raw_records(self, site: str, date: str) -> list:
        return self.get(
            "raw-files",
            params={
                "instrument": ["halo-doppler-lidar", "wls100s", "wls200s", "wls400s"],
                "site": site,
                "date": date,
            },
        )

    def get_record_content(self, rec: dict) -> io.BytesIO:
        if self.cache:
            return cached_record(rec, self.session)
        content = self.session.get(rec["downloadUrl"]).content
        if rec["filename"].endswith(".gz"):
            content = gzip.decompress(content)
        return io.BytesIO(content)
