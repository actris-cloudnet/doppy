import asyncio
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import aiohttp
from tqdm.asyncio import tqdm


@dataclass
class Record:
    uuid: str
    checksum: str
    filename: str
    s3key: str
    measurement_date: str
    size: int
    status: str
    created_at: str
    updated_at: str
    instrument_pid: str
    tags: list[str]
    site_id: str
    instrument_id: str
    instrument_type: str
    instrument_info_uuid: str
    download_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "Record":
        return cls(
            uuid=data["uuid"],
            checksum=data["checksum"],
            filename=data["filename"],
            s3key=data["s3key"],
            measurement_date=data["measurementDate"],
            size=int(data.get("size", 0)),
            status=data["status"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            instrument_pid=data["instrumentPid"],
            tags=data.get("tags", []),
            site_id=data.get("siteId", ""),
            instrument_id=data.get("instrumentId", ""),
            instrument_type=data.get("instrument", {}).get("type", ""),
            instrument_info_uuid=data.get("instrumentInfoUuid", ""),
            download_url=data.get("downloadUrl", ""),
        )

    def as_path(self) -> Path:
        return Path(
            f"data/{self.site_id}/{self.measurement_date}/{self.instrument_id}/{self.uuid[:6]}/{self.filename}"
        )


class Dataset:
    def __init__(self, site: str, date: str, instrument_type: str | set[str] | None):
        if instrument_type is None:
            instrument_types = set()
        elif isinstance(instrument_type, str):
            instrument_types = {instrument_type}
        else:
            instrument_types = instrument_type

        all_records = [
            Record.from_dict(r) for r in asyncio.run(self.fetch_records(site, date))
        ]
        self.records = (
            all_records
            if instrument_types is None
            else [rec for rec in all_records if rec.instrument_type in instrument_types]
        )

        self.semaphore = asyncio.Semaphore(4)
        asyncio.run(self.download_all_records())

    async def fetch_records(self, site: str, date: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://cloudnet.fmi.fi/api/raw-files",
                params={"site": site, "date": date},
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(
                        f"API request failed with status {resp.status}: {error_text}"
                    )
                return await resp.json()

    async def download_file(self, session: aiohttp.ClientSession, record: Record):
        async with self.semaphore:
            if not record.download_url:
                return

            dest_path = record.as_path()
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if dest_path.exists():
                return

            attempt = 0
            max_retries = 5
            last_exception = None

            while attempt <= max_retries:
                try:
                    async with session.get(record.download_url) as response:
                        if response.status == 200:
                            with open(dest_path, "wb") as file:
                                while chunk := await response.content.read(1024):
                                    file.write(chunk)
                            return
                        elif 400 <= response.status < 500:
                            raise Exception(
                                f"Client error {response.status} for {record.filename}"
                            )
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_exception = e

                if attempt < max_retries:
                    delay = (2**attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)

                attempt += 1

            if last_exception is not None:
                raise last_exception
            raise RuntimeError("Unreachable")

    async def download_all_records(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.download_file(session, record) for record in self.records]
            await tqdm.gather(*tasks, desc="Downloading files:", ncols=120)

    def iter(self) -> Iterator[tuple[Record, Path]]:
        return ((record, record.as_path()) for record in self.records)
