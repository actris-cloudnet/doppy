"""
Compare NoiseMaskMethod variants on the Neumayer StreamLine XR+.

The instrument has a radial-velocity noise peak around -1 m/s at SNR < -22 dB,
documented in Erdmann & Gasch (2026), Appendix D.
https://doi.org/10.5194/gmd-19-2497-2026
"""

import argparse

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from dataset import Dataset
from matplotlib.axes import Axes

import doppy
from doppy.options import BgCorrectionMethod, NoiseMaskMethod


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare HALO stare noise masks on Neumayer data"
    )
    parser.add_argument("--site", default="neumayer")
    parser.add_argument("--date", default="2026-03-31")
    args = parser.parse_args()

    data = Dataset(site=args.site, date=args.date, instrument_type="Doppler lidar")
    paths = []
    paths_bg = []
    for record, path in data.iter():
        # Mirrors cloudnet-processing's ProcessDopplerLidar.process_halo:
        # co stare HPL files start with "Stare" and must not carry the "cross" tag
        # (otherwise non-stare scans like User5 wind modes and cross-pol beams
        # leak in and corrupt velocity output).
        if record.filename.startswith("Background"):
            paths_bg.append(path)
        elif (
            record.filename.startswith("Stare")
            and record.filename.endswith(".hpl")
            and "cross" not in record.tags
        ):
            paths.append(path)

    default = doppy.product.Stare.from_halo_data(
        data=paths,
        data_bg=paths_bg,
        bg_correction_method=BgCorrectionMethod.FIT,
    )
    intensity_only = doppy.product.Stare.from_halo_data(
        data=paths,
        data_bg=paths_bg,
        bg_correction_method=BgCorrectionMethod.FIT,
        noise_mask_method=NoiseMaskMethod.INTENSITY_ONLY,
    )

    _print_stats("default", default)
    _print_stats("intensity_only", intensity_only)
    _assert_invariants(default, intensity_only)
    _plot(default, intensity_only)


def _print_stats(label: str, stare: doppy.product.Stare) -> None:
    total = stare.mask_beta.size
    beta_masked = int(stare.mask_beta.sum())
    rv_masked = int(stare.mask_radial_velocity.sum())
    print(
        f"[{label}] beta masked: {beta_masked}/{total} "
        f"({beta_masked / total:.1%}), "
        f"v masked: {rv_masked}/{total} ({rv_masked / total:.1%})"
    )


def _assert_invariants(
    default: doppy.product.Stare, intensity_only: doppy.product.Stare
) -> None:
    assert np.array_equal(
        intensity_only.mask_radial_velocity, intensity_only.mask_beta
    ), "intensity_only should reuse mask_beta for mask_radial_velocity"
    assert default.mask_beta.shape == intensity_only.mask_beta.shape
    if np.array_equal(default.mask_beta, intensity_only.mask_beta):
        print("WARN: masks are identical — new path produced no change")


def _plot(default: doppy.product.Stare, intensity_only: doppy.product.Stare) -> None:
    fig, ax = plt.subplots(3, 2, sharex="col", sharey="row")
    panels = [
        (0, default, "default (intensity & velocity)"),
        (1, intensity_only, "intensity_only"),
    ]
    for col, stare, title in panels:
        ax[0, col].set_title(title)
        ax[0, col].pcolormesh(
            stare.time,
            stare.radial_distance,
            np.ma.masked_array(stare.beta, stare.mask_beta).T,
            norm=matplotlib.colors.LogNorm(vmin=1e-7, vmax=1e-4),
            rasterized=True,
            cmap="plasma",
        )
        ax[1, col].pcolormesh(
            stare.time,
            stare.radial_distance,
            stare.mask_beta.T.astype(float),
            vmin=0,
            vmax=1,
            rasterized=True,
            cmap="Greys",
        )
        ax[2, col].pcolormesh(
            stare.time,
            stare.radial_distance,
            np.ma.masked_array(stare.radial_velocity, stare.mask_radial_velocity).T,
            vmin=-2,
            vmax=2,
            rasterized=True,
            cmap="coolwarm",
        )
    ax[0, 0].set_ylabel("beta (masked)")
    ax[1, 0].set_ylabel("mask_beta")
    ax[2, 0].set_ylabel("v (masked)")

    fig.set_size_inches(18, 10)
    fig.subplots_adjust(
        left=0.05, right=0.99, top=0.96, bottom=0.05, wspace=0.075, hspace=0.1
    )

    for axis in ax.ravel():
        _set_time_axis(axis)
        _set_axis_style(axis)

    plt.show()


def _set_axis_style(ax: Axes) -> None:
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["bottom"].set_position(("outward", 2))
    ax.spines["left"].set_position(("outward", 2))


def _set_time_axis(ax: Axes) -> None:
    locator = matplotlib.dates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(matplotlib.dates.ConciseDateFormatter(locator))


if __name__ == "__main__":
    main()
