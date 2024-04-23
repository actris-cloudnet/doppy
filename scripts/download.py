# type: ignore
import argparse
import datetime
from pathlib import Path

import requests


def download_files(api_url, instrument, site, start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        print(f"Downloading files for {current_date}...")
        response = requests.get(
            f"{api_url}?instrument={instrument}&site={site}&date={current_date}"
        )
        for item in response.json():
            download_url = item["downloadUrl"]
            site_id = item["siteId"]
            measurement_date = item["measurementDate"]
            dir_path = Path("data", site_id, measurement_date, *item["tags"])
            dir_path.mkdir(parents=True, exist_ok=True)
            filename = item["filename"]
            print(f"Downloading {filename} to {dir_path}...")
            file_response = requests.get(download_url)
            with open(dir_path / filename, "wb") as file:
                file.write(file_response.content)
        current_date += datetime.timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description="Download files from API")
    parser.add_argument("--site", required=True, help="Site name")
    parser.add_argument("--instrument", required=True, help="Instrument name")
    parser.add_argument("--date", help="Specific date (YYYY-MM-DD)")
    parser.add_argument(
        "--date-range", nargs=2, help="Start and end date (YYYY-MM-DD YYYY-MM-DD)"
    )
    args = parser.parse_args()

    if args.date:
        start_date = end_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    elif args.date_range:
        start_date = datetime.datetime.strptime(args.date_range[0], "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(args.date_range[1], "%Y-%m-%d").date()

    api_url = "https://cloudnet.fmi.fi/api/raw-files"
    download_files(api_url, args.instrument, args.site, start_date, end_date)


if __name__ == "__main__":
    main()
