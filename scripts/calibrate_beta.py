import argparse
import re
from io import BytesIO

import devboard as db
import doppy
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import requests
import scipy
import xarray as xr
from doppy.data.api import Api


def main():
    api = Api(cache=True)
    args = _get_args()

    # stare, raw = _get_stare(args, api)

    # ref_lidar = _get_lidar(args, api)
    # db.utils.cache_save(stare, raw, ref_lidar)
    stare, raw, ref_lidar = db.utils.cache_load()

    beta_ref_aligned, beta_screened_ref_aligned = align_reference_beta(
        raw, stare, ref_lidar
    )

    _interactive(raw, beta_ref_aligned)

    # _plot_betas(raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned)

    # _calibrate_telescope(
    #    raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned
    # )


def _calibrate_telescope(
    raw, stare, ref_lidar, beta_ref_aligned, beta_screened_ref_aligned
):
    # mask = stare.mask | np.isnan(beta_screened_ref_aligned)
    mask = np.isnan(beta_screened_ref_aligned)
    cnr = raw.cnr[~mask]
    target_beta = beta_ref_aligned[~mask]
    radial_distance = np.broadcast_to(raw.radial_distance, mask.shape)[~mask]
    wavelength = doppy.defaults.WindCube.wavelength
    effective_diameter_of_gaussian_beam_init = 25e-3  # 0.09308979591836734
    focus_init = 500  # 5741.939393939394

    def beta_func(focus, diam, e, b):
        return _compute_beta(cnr, radial_distance, focus, wavelength, diam, e, b)

    d_guess = np.linspace(0.04, 0.1, 50)
    f_guess = np.linspace(300, 600, 10)

    # d_guess = np.linspace(0.01, 0.2, 200)
    # f_guess = np.linspace(5740, 5744, 3)

    # D, F = np.meshgrid(d_guess, f_guess, indexing="ij")

    # def _beta_wrap(i, j):
    #    beta_hat = beta_func(F[i, j], D[i, j])
    #    return np.sqrt(((target_beta - beta_hat) ** 2).mean())

    # RMSE = np.fromfunction(np.vectorize(_beta_wrap), D.shape, dtype=int)

    # res = np.unravel_index(RMSE.argmin(), RMSE.shape)

    # d_min = D[res]
    # f_min = F[res]
    # rmse_min = RMSE[res]

    # fig, ax = plt.subplots(figsize=(15, 10))
    # cbar_opts = {
    #    "orientation": "horizontal",
    #    "pad": 0.05,
    #    "aspect": 70,
    #    "fraction": 0.05,
    # }

    # cax = ax.pcolormesh(D, F, RMSE, shading="auto", cmap="viridis")
    # ax.scatter(d_min, f_min, s=20, c="red")
    # ax.set_xlabel("diameter")
    # ax.set_ylabel("focus")

    # print(f"diameter: {d_min}, focus: {f_min}, rmse: {rmse_min}")

    # fig.colorbar(cax, ax=ax, **cbar_opts)

    # db.add_fig(fig)

    def _beta_rmse_func(x):
        focus, diam, e, b = x
        beta_hat = beta_func(focus, diam, e, b)
        return np.sqrt(((target_beta - beta_hat) ** 2).mean())

    f_init = 1e5
    d_init = 0.02
    e_init = 1e-5
    b_init = 5e7
    x0 = [f_init, d_init, e_init, b_init]
    bounds = [
        (f_init / 10, f_init * 10),
        (d_init / 10, d_init * 10),
        (e_init / 10, e_init * 10),
        (b_init / 10, b_init * 10),
    ]
    res = scipy.optimize.minimize(_beta_rmse_func, x0, bounds=bounds)
    focus_min, diam_min, e_min, b_min = res.x

    beta_hat = beta_func(focus_min, diam_min, e_min, b_min)

    fig, ax = plt.subplots(figsize=(15, 10))

    rind = np.random.choice(len(beta_hat), size=100)
    ax.scatter(target_beta[rind], beta_hat[rind], alpha=0.1)
    ax.set_xscale("log")
    ax.set_yscale("log")

    db.add_fig(fig)

    fig, ax = plt.subplots(2, figsize=(15, 10))

    ax[0].hist(target_beta)
    ax[1].hist(beta_hat)

    db.add_fig(fig)
    print(res)

    # compute new beta

    beta_calibrated = _compute_beta(
        raw.cnr, raw.radial_distance, focus_min, wavelength, diam_min, e_min, b_min
    )

    opts_beta = {
        "origin": "lower",
        "aspect": "auto",
        "norm": mpl.colors.LogNorm(vmin=1e-7, vmax=1e-4),
    }
    opts_cnr = {
        "origin": "lower",
        "aspect": "auto",
        "norm": mpl.colors.LogNorm(vmin=1e-4, vmax=1e-2),
    }
    opts_velocity = {
        "origin": "lower",
        "aspect": "auto",
        "vmin": -4,
        "vmax": 4,
        "cmap": "coolwarm",
        # "norm": mpl.colors.LogNorm(vmin=1e-7, vmax=1e-4),
    }
    cbar_opts = {
        "orientation": "horizontal",
        "pad": 0.07,
        "aspect": 70,
        "fraction": 0.05,
    }

    fig, ax = plt.subplots(4, figsize=(15, 20))
    fig.subplots_adjust(
        left=0.05, right=0.98, top=0.99, bottom=0.01, wspace=0.1, hspace=0.1
    )

    cax = ax[0].imshow(ref_lidar.beta.data.T, **opts_beta)
    fig.colorbar(cax, ax=ax[0], **cbar_opts)

    cax = ax[1].imshow(beta_calibrated.T, **opts_beta)
    fig.colorbar(cax, ax=ax[1], **cbar_opts)

    cax = ax[2].imshow(10 ** (raw.cnr / 10).T, **opts_cnr)
    fig.colorbar(cax, ax=ax[2], **cbar_opts)

    cax = ax[3].imshow(raw.radial_velocity.T, **opts_velocity)
    fig.colorbar(cax, ax=ax[3], **cbar_opts)

    db.add_fig(fig)
    plt.close("all")

    breakpoint()
    pass


def _interactive(raw, beta_ref):
    from matplotlib.widgets import Slider

    d_init = 2.611e-01
    f_init = 1.055e03
    e_init = 1e-5
    b_init = 5e7
    wavelength = doppy.defaults.WindCube.wavelength

    fig, ax = plt.subplots(3, 1, figsize=(16, 11))
    plt.subplots_adjust(
        left=0.05, right=0.98, top=0.95, bottom=0.3, wspace=0.1, hspace=0.1
    )
    axcolor = "lightgoldenrodyellow"
    ax_d = plt.axes([0.1, 0.05, 0.7, 0.03], facecolor=axcolor)
    ax_f = plt.axes([0.1, 0.10, 0.7, 0.03], facecolor=axcolor)
    ax_e = plt.axes([0.1, 0.15, 0.7, 0.03], facecolor=axcolor)
    ax_b = plt.axes([0.1, 0.20, 0.7, 0.03], facecolor=axcolor)
    slider_d = Slider(ax_d, "Diameter", d_init / 10, 10 * d_init, valinit=d_init)
    slider_f = Slider(ax_f, "focus", f_init / 10, 10 * f_init, valinit=f_init)
    slider_e = Slider(ax_e, "E", e_init / 20, 20 * e_init, valinit=e_init)
    slider_b = Slider(ax_b, "B", b_init / 20, 20 * b_init, valinit=b_init)

    beta = _compute_beta(
        raw.cnr, raw.radial_distance, f_init, wavelength, d_init, e_init, b_init
    )

    opts_beta = {
        "origin": "lower",
        "aspect": "auto",
        "norm": mpl.colors.LogNorm(vmin=1e-7, vmax=1e-4),
    }
    opts_cnr = {
        "origin": "lower",
        "aspect": "auto",
        "norm": mpl.colors.LogNorm(vmin=1e-4, vmax=1e-2),
    }
    cbar_opts = {
        "orientation": "horizontal",
        "pad": 0.07,
        "aspect": 70,
        "fraction": 0.05,
    }

    cax_beta = ax[0].imshow(beta.T, **opts_beta)
    fig.colorbar(cax_beta, ax=ax[0], **cbar_opts)
    cax_beta_ref = ax[1].imshow(beta_ref.T, **opts_beta)
    fig.colorbar(cax_beta_ref, ax=ax[1], **cbar_opts)

    cax_cnr = ax[2].imshow(10 ** (0.1 * raw.cnr.T), **opts_cnr)
    fig.colorbar(cax_cnr, ax=ax[2], **cbar_opts)

    def _update(val):
        d = slider_d.val
        f = slider_f.val
        e = slider_e.val
        b = slider_b.val
        beta_new = _compute_beta(raw.cnr, raw.radial_distance, f, wavelength, d, e, b)
        cax_beta.set_data(beta_new.T)

    slider_d.on_changed(_update)
    slider_f.on_changed(_update)
    slider_e.on_changed(_update)
    slider_b.on_changed(_update)
    plt.show()


def _compute_beta(
    cnr: npt.NDArray[np.float64],
    radial_distance: npt.NDArray[np.float64],
    focus: float,
    wavelength: float,
    effective_diameter_of_gaussian_beam,
    E,
    B,
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

    snr = 10 ** (cnr / 10)
    h = scipy.constants.Planck
    c = scipy.constants.speed_of_light
    eta = 1
    # E = 1e-5
    # B = 5e7
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
