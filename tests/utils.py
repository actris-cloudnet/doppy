from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from uuid import UUID

import tomli


class TestType(str, Enum):
    Raw = "Raw"
    Stare = "Stare"
    Wind = "Wind"


@dataclass(order=True)
class Testfile:
    site_id: str
    filename: str
    measurement_date: date
    instrument_id: str
    uuid: UUID
    checksum: str
    instrument_uuid: UUID
    download_url: str


@dataclass(order=True)
class Testcase:
    type: TestType
    description: str | None = None
    files: list[Testfile] = field(default_factory=list)


@dataclass
class Tests:
    testcase: list[Testcase]


def parse_tests_toml(filepath: Path) -> Tests:
    with open(filepath, "rb") as f:
        data = tomli.load(f)

    testcases = []
    for entry in data.get("testcase", []):
        test_type = TestType(entry["type"])
        description = entry.get("description")

        files = []
        for file_entry in entry["files"]:
            testfile = Testfile(
                site_id=file_entry["site_id"],
                filename=file_entry["filename"],
                measurement_date=date.fromisoformat(file_entry["measurement_date"]),
                instrument_id=file_entry["instrument_id"],
                uuid=UUID(file_entry["uuid"]),
                checksum=file_entry["checksum"],
                instrument_uuid=UUID(file_entry["instrument_uuid"]),
                download_url=file_entry["download_url"],
            )
            files.append(testfile)

        testcases.append(Testcase(type=test_type, description=description, files=files))

    return Tests(testcase=testcases)


def testfiles_to_paths(testfiles: list[Testfile]) -> list[Path]:
    return [testfile_to_path(f) for f in testfiles]


def testfile_to_path(testfile: Testfile) -> Path:
    return (
        Path(__file__).parent
        / "data"
        / testfile.site_id
        / str(testfile.uuid)[:8]
        / testfile.filename
    )
