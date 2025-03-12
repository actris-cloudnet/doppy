import doppy
from dataset import Dataset


def test_cluj():
    data = Dataset(site="cluj", date="2024-11-01", instrument_type="doppler-lidar")

    paths = []
    paths_bg = []
    for record, path in data.iter():
        if record.filename.startswith("Stare"):
            paths.append(path)
        elif record.filename.startswith("Background"):
            paths_bg.append(path)
    doppy.product.Stare.from_halo_data(
        paths, paths_bg, doppy.options.BgCorrectionMethod.FIT
    )


if __name__ == "__main__":
    test_cluj()
