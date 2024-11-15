import argparse
import re
from io import BytesIO

import devboard as db
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import requests
import scipy
import xarray as xr

import doppy
from doppy.data.api import Api


def main():
    api = Api(cache=True)
    args = _get_args()
    stare, raw = _get_stare(args, api)
    # ref_lidar = _get_lidar(args, api)
    # db.utils.cache_save(stare, raw, ref_lidar)
    stare, raw, ref_lidar = db.utils.cache_load()
    beta_ref_aligned, beta_screened_ref_aligned = align_reference_beta(
        raw, stare, ref_lidar
    )

    # _plot_betas(raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned)

    _calibrate_telescope(
        raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned
    )


def _calibrate_telescope(
    raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned
):
    mask = stare.mask | np.isnan(beta_screened_ref_aligned)

    cnr = raw.cnr[~mask]
    target_beta = beta_ref_aligned[~mask]
    radial_distance = np.broadcast_to(raw.radial_distance,mask.shape)[~mask]
    wavelength = doppy.defaults.WindCube.wavelength
    effective_diameter_of_gaussian_beam_init = 25e-3
    def beta_func(focus,diam):
        _compute_beta(cnr,radial_distance,focus, wavelength, diam)


def _compute_beta(
    intensity: npt.NDArray[np.float64],
    radial_distance: npt.NDArray[np.float64],
    focus: float,
    wavelength: float,
    effective_diameter_of_gaussian_beam,
) -> npt.NDArray[np.float64]:
    """
    Parameters
    ----------
    radial_distance
        distance from the instrument
    focus
        focal length of the telescope for the transmitter and receiver
    wavelength
        laser wavelength

    Local variables
    ---------------
    eta
        detector quantum efficiency
    E
        beam energy
    nu
        optical frequency
    h
        planc's constant
    c
        speed of light
    B
        receiver bandwidth

    References
    ----------
    Methodology for deriving the telescope focus function and
    its uncertainty for a heterodyne pulsed Doppler lidar
        authors:  Pyry Pentikäinen, Ewan James O'Connor,
            Antti Juhani Manninen, and Pablo Ortiz-Amezcua
        doi: https://doi.org/10.5194/amt-13-2849-2020
    """

    snr = intensity - 1
    h = scipy.constants.Planck
    c = scipy.constants.speed_of_light
    eta = 1
    E = 1e-5
    B = 5e7
    nu = c / wavelength
    A_e = _compute_effective_receiver_energy(
        radial_distance, focus, wavelength, effective_diameter_of_gaussian_beam
    )
    beta = 2 * h * nu * B * radial_distance**2 * snr / (eta * c * E * A_e)
    return np.array(beta, dtype=np.float64)


def _compute_effective_receiver_energy(
    radial_distance: npt.NDArray[np.float64],
    focus: float,
    wavelength: float,
    effective_diameter_of_gaussian_beam: float,
) -> npt.NDArray[np.float64]:
    """
    NOTE
    ----
    Using uncalibrated values from https://doi.org/10.5194/amt-13-2849-2020


    Parameters
    ----------
    radial_distance
        distance from the instrument
    focus
        effective focal length of the telescope for the transmitter and receiver
    wavelength
        laser wavelength
    """
    # D = 25e-3  # effective_diameter_of_gaussian_beam
    D = effective_diameter_of_gaussian_beam
    return np.array(
        np.pi
        * D**2
        / (
            4
            * (
                1
                + (np.pi * D**2 / (4 * wavelength * radial_distance)) ** 2
                * (1 - radial_distance / focus) ** 2
            )
        ),
        dtype=np.float64,
    )


def _plot_betas(raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned):
    nfigs = 6
    fig, ax = plt.subplots(nfigs, 1, figsize=(25, nfigs * 10))
    fig.subplots_adjust(
        left=0.05, right=0.98, top=0.99, bottom=0.01, wspace=0.1, hspace=0.1
    )
    opts = {
        "origin": "lower",
        "aspect": "auto",
        "norm": mpl.colors.LogNorm(vmin=1e-7, vmax=1e-4),
    }
    cbar_opts = {
        "orientation": "horizontal",
        "pad": 0.05,
        "aspect": 70,
        "fraction": 0.05,
    }
    i = 0

    mask = stare.mask | np.isnan(beta_screened_ref_aligned)

    rel_offset = np.median(beta_ref_aligned[~mask] / raw.relative_beta[~mask])

    cax = ax[i].imshow(rel_offset * raw.relative_beta.T, **opts)
    fig.colorbar(cax, ax=ax[i], **cbar_opts)
    i += 1

    cax = ax[i].imshow(beta_ref_aligned.T, **opts)
    fig.colorbar(cax, ax=ax[i], **cbar_opts)
    i += 1

    cax = ax[i].imshow(
        np.ma.masked_where(mask, raw.relative_beta).T,
        **opts,
    )
    fig.colorbar(cax, ax=ax[i], **cbar_opts)
    i += 1

    cax = ax[i].imshow(
        np.ma.masked_where(mask, beta_ref_aligned).T,
        **opts,
    )
    fig.colorbar(cax, ax=ax[i], **cbar_opts)
    i += 1

    rind = np.random.choice(len(beta_ref_aligned[~mask]), size=1000)
    ax[i].scatter(
        beta_ref_aligned[~mask][rind], raw.relative_beta[~mask][rind], alpha=0.1
    )
    ax[i].set_xscale("log")
    ax[i].set_yscale("log")
    i += 1

    ax[i].hexbin(
        beta_ref_aligned[~mask],
        raw.relative_beta[~mask],
        gridsize=200,
        xscale="log",
        yscale="log",
        # bins="log",
        cmap="plasma",
    )
    i += 1

    db.add_fig(fig)


def align_reference_beta(raw, stare, ref_lidar):
    if stare.time.dtype != np.dtype("datetime64[us]"):
        raise TypeError("stare.time expected to be datetime64[us]")
    beta_interp = interpolate(
        ref_lidar.beta_raw.data,
        ref_lidar.time.data.astype("datetime64[us]"),
        ref_lidar.height.data,
        raw.time,
        raw.radial_distance + ref_lidar["altitude"].data,
    )
    beta_interp_screened = interpolate(
        ref_lidar.beta.data,
        ref_lidar.time.data.astype("datetime64[us]"),
        ref_lidar.height.data,
        raw.time,
        raw.radial_distance + ref_lidar["altitude"].data,
    )
    return beta_interp, beta_interp_screened


def interpolate(Z, x, y, x_target, y_target):
    interpolator = scipy.interpolate.RegularGridInterpolator(
        (x, y),
        Z,
        method="nearest",
        bounds_error=False,
        fill_value=None,
    )
    X, Y = np.meshgrid(x_target, y_target, indexing="ij")
    Z_target = interpolator((X, Y))
    return Z_target


def _plot_stare(stare):
    fig, ax = db.plt.subplots(figsize=(20, 10))
    ax.imshow(
        stare.radial_velocity.T,
        aspect="auto",
        origin="lower",
        vmin=-4,
        vmax=4,
        cmap="coolwarm",
    )
    db.add_fig(fig)

    fig, ax = db.plt.subplots(figsize=(20, 10))
    ax.imshow(
        db.np.ma.masked_where(stare.mask, stare.radial_velocity).T,
        aspect="auto",
        origin="lower",
        vmin=-4,
        vmax=4,
        cmap="coolwarm",
    )
    db.add_fig(fig)

    fig, ax = db.plt.subplots(figsize=(20, 10))
    ax.imshow(
        db.np.ma.masked_where(stare.mask, stare.beta).T,
        aspect="auto",
        origin="lower",
        norm=db.mpl.colors.LogNorm(vmin=1e-9, vmax=1e-7),
    )
    db.add_fig(fig)

    fig, ax = db.plt.subplots(figsize=(20, 10))
    ax.imshow(
        stare.beta.T,
        aspect="auto",
        origin="lower",
        norm=db.mpl.colors.LogNorm(vmin=1e-9, vmax=1e-7),
    )
    db.add_fig(fig)

    breakpoint()
    pass


def _get_stare(args, api):
    records = api.get(
        "raw-files",
        {
            "site": args.site,
            "instrumentPid": args.cal_pid,
            "dateFrom": args.date_from,
            "dateTo": args.date_to,
        },
    )

    r = re.compile(r".*fixed.*", re.IGNORECASE)
    records_fixed = [rec for rec in records if r.match(rec["filename"])]
    data = [api.get_record_content(r) for r in records_fixed]
    raws = doppy.raw.WindCubeFixed.from_srcs(data)
    for d in data:
        d.seek(0)
    raw = doppy.raw.WindCubeFixed.merge(raws).sorted_by_time().nan_profiles_removed()
    stare = doppy.product.Stare.from_windcube_data(
        data=data,
    )
    return stare, raw


def _get_lidar(args, api):
    resp = api.get(
        "files",
        {
            "site": args.site,
            "instrumentPid": args.ref_pid,
            "dateFrom": args.date_from,
            "dateTo": args.date_to,
            "product": "lidar",
        },
    )
    if len(resp) != 1:
        raise ValueError("Expected only one lidar file")
    nc_content = requests.get(resp[0]["downloadUrl"]).content
    lidar = xr.open_dataset(BytesIO(nc_content))
    return lidar


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument(
        "--cal-pid",
        required=True,
        help="PID for instrument that needs to be calibrated",
    )
    parser.add_argument(
        "--ref-pid",
        required=True,
        help="PID for the reference instrument that is used for calibration",
    )
    parser.add_argument("--date-from", required=True)
    parser.add_argument("--date-to", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
