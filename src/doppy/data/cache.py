import gzip
import shutil
from io import BytesIO
from pathlib import Path

from requests import Session


def cached_record(
    record: dict, session: Session, check_disk_usage: bool = True
) -> BytesIO:
    cache_dir = Path("cache")
    path = cache_dir / record["uuid"]

    if check_disk_usage:
        HUNDRED_GIGABYTES_AS_BYTES = 100 * 1024 * 1024 * 1024

        _, _, disk_free = shutil.disk_usage("./")
        if disk_free < HUNDRED_GIGABYTES_AS_BYTES:
            _clear_dir(cache_dir)

    if path.is_file():
        return BytesIO(path.read_bytes())
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = session.get(record["downloadUrl"]).content
        if record["filename"].endswith(".gz"):
            content = gzip.decompress(content)
        with path.open("wb") as f:
            f.write(content)
        return BytesIO(content)


def _clear_dir(path: Path) -> None:
    for f in path.glob("**/*"):
        if f.is_file():
            f.unlink()
