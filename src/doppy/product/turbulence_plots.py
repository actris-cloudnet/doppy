# type: ignore
from __future__ import annotations

import devboard as devb
import matplotlib.colors
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import Collection
from matplotlib.lines import Line2D

from doppy.product.stare import Stare
from doppy.product.utils import VarResult


def plot_var_res(r: VarResult, stare: Stare):
    fig, ax = plt.subplots()

    window = (r.window_stop - r.window_start).astype(float) * 1e-6 / 60
    mesh = ax.pcolormesh(
        stare.time,
        stare.radial_distance,
        window.T,
        norm=matplotlib.colors.LogNorm(vmin=1 / 60, vmax=window.max()),
    )
    fig.colorbar(mesh, ax=ax)

    devb.add_fig(fig)


def plot_dr(vert, dr):
    fig, ax = plt.subplots(2)
    range_mask = vert.height < 4000

    mesh = ax[0].pcolormesh(
        vert.time,
        vert.height[range_mask],
        dr[:, range_mask].T,
        norm=matplotlib.colors.LogNorm(vmin=1e-6, vmax=1e-1),
        cmap="plasma",
    )
    fig.colorbar(
        mesh, ax=ax[0], orientation="horizontal", shrink=0.5, pad=0.1
    ).outline.set_visible(False)  # type: ignore

    mesh = ax[1].pcolormesh(
        vert.time,
        vert.height[range_mask],
        vert.w[:, range_mask].T,
        cmap="coolwarm",
        vmin=-4,
        vmax=4,
    )

    fig.colorbar(
        mesh, ax=ax[1], orientation="horizontal", shrink=0.5, pad=0.1
    ).outline.set_visible(False)  # type: ignore

    locator = matplotlib.dates.AutoDateLocator()

    for i in range(len(ax)):
        ax[i].xaxis.set_major_locator(locator)
        ax[i].xaxis.set_major_formatter(matplotlib.dates.ConciseDateFormatter(locator))
        ax[i].spines["left"].set_visible(False)
        ax[i].spines["top"].set_visible(False)
        ax[i].spines["right"].set_visible(False)
        ax[i].spines["bottom"].set_visible(False)

    fig.set_size_inches(22, 16)
    fig.tight_layout()

    # _rasterize(ax)
    # fig.savefig(f"plots/noise/{title}.pdf")
    devb.add_fig(fig)
    plt.close("all")


def plot_dr_old(stare, dr, title):
    fig, ax = plt.subplots(2)
    range_mask = stare.radial_distance < 4000

    mesh = ax[0].pcolormesh(
        stare.time,
        stare.radial_distance[range_mask],
        dr[:, range_mask].T,
        norm=matplotlib.colors.LogNorm(vmin=1e-6, vmax=1e-1),
        cmap="plasma",
    )
    fig.colorbar(
        mesh, ax=ax[0], orientation="horizontal", shrink=0.5, pad=0.1
    ).outline.set_visible(False)  # type: ignore

    mesh = ax[1].pcolormesh(
        stare.time,
        stare.radial_distance[range_mask],
        stare.radial_velocity[:, range_mask].T,
        cmap="coolwarm",
        vmin=-4,
        vmax=4,
    )

    fig.colorbar(
        mesh, ax=ax[1], orientation="horizontal", shrink=0.5, pad=0.1
    ).outline.set_visible(False)  # type: ignore

    locator = matplotlib.dates.AutoDateLocator()

    ax[0].set_title(title)
    for i in range(len(ax)):
        ax[i].xaxis.set_major_locator(locator)
        ax[i].xaxis.set_major_formatter(matplotlib.dates.ConciseDateFormatter(locator))
        ax[i].spines["left"].set_visible(False)
        ax[i].spines["top"].set_visible(False)
        ax[i].spines["right"].set_visible(False)
        ax[i].spines["bottom"].set_visible(False)

    fig.set_size_inches(22, 16)
    fig.tight_layout()

    # _rasterize(ax)
    # fig.savefig(f"plots/noise/{title}.pdf")
    devb.add_fig(fig)
    plt.close("all")


def _rasterize(ax):
    for a in ax:
        for artist in a.get_children():
            if isinstance(artist, (Line2D, Collection)):
                artist.set_rasterized(True)


def plot_interpolaterd_wind(stare, wind, iwind):
    fig, ax = plt.subplots(3)
    wspeed = np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2)
    ax[0].pcolormesh(wind.time, wind.height, wspeed.T)
    ax[1].pcolormesh(wind.time, wind.height, wind.mask.T)

    ax[2].pcolormesh(stare.time, stare.radial_distance, iwind.T)

    devb.add_fig(fig)


def plot_next_valid(N):
    fig, ax = plt.subplots()
    ax.plot(N)
    devb.add_fig(fig)


def plot_var(var, stare):
    fig, ax = plt.subplots()

    ax.pcolormesh(stare.time, stare.radial_distance, var.T)
    devb.add_fig(fig)


def plot_interpolated_mask(stare, wind, mask):
    fig, ax = plt.subplots()
    pmesh = ax.pcolormesh(stare.time, stare.radial_distance, mask.T)
    ax.set_title("mask")

    devb.add_fig(fig)
