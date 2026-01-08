import doppy
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from dataset import Dataset
from matplotlib.axes import Axes


def quick_dbq() -> None:
    site = "warsaw"
    date = "2026-01-01"
    data = Dataset(site=site, date=date, instrument_type="Doppler lidar")

    paths = []
    paths_bg = []
    for record, path in data.iter():
        if record.filename.startswith("Stare"):
            paths.append(path)
        elif record.filename.startswith("Background"):
            paths_bg.append(path)
    stare = doppy.product.Stare.from_halo_data(
        paths, paths_bg, doppy.options.BgCorrectionMethod.FIT
    )
    show(stare)


def show(stare: doppy.product.Stare) -> None:
    fig, ax = plt.subplots(3, 2, sharex="col", sharey="row")
    ax[0, 0].pcolormesh(
        stare.time,
        stare.radial_distance,
        stare.snr.T,
        norm=matplotlib.colors.LogNorm(1e-3, 1),
        rasterized=True,
        cmap="plasma",
    )
    ax[0, 1].pcolormesh(
        stare.time,
        stare.radial_distance,
        np.ma.masked_array(stare.snr, stare.mask_beta).T,
        norm=matplotlib.colors.LogNorm(1e-3, 1),
        rasterized=True,
        cmap="plasma",
    )
    ax[1, 0].pcolormesh(
        stare.time,
        stare.radial_distance,
        stare.beta.T,
        norm=matplotlib.colors.LogNorm(vmin=1e-7, vmax=1e-4),
        rasterized=True,
        cmap="plasma",
    )
    ax[1, 1].pcolormesh(
        stare.time,
        stare.radial_distance,
        np.ma.masked_array(stare.beta, stare.mask_beta).T,
        norm=matplotlib.colors.LogNorm(vmin=1e-7, vmax=1e-4),
        rasterized=True,
        cmap="plasma",
    )
    ax[2, 0].pcolormesh(
        stare.time,
        stare.radial_distance,
        stare.radial_velocity.T,
        vmin=-2,
        vmax=2,
        rasterized=True,
        cmap="coolwarm",
    )
    ax[2, 1].pcolormesh(
        stare.time,
        stare.radial_distance,
        np.ma.masked_array(stare.radial_velocity, stare.mask_radial_velocity).T,
        vmin=-2,
        vmax=2,
        rasterized=True,
        cmap="coolwarm",
    )

    fig.set_size_inches(18, 10)
    fig.subplots_adjust(
        left=0.05, right=0.99, top=0.96, bottom=0.05, wspace=0.075, hspace=0.1
    )

    for axis in ax.ravel():
        _set_time_axis(axis)
        _set_axis_style(axis)

    plt.show()


def _set_axis_style(ax: Axes):
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["bottom"].set_position(("outward", 2))
    ax.spines["left"].set_position(("outward", 2))


def _set_time_axis(ax: Axes):
    locator = matplotlib.dates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(matplotlib.dates.ConciseDateFormatter(locator))


if __name__ == "__main__":
    quick_dbq()
