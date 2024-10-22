import devboard as db
import numpy as np
import polars as pl
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from doppy.raw.windcube import WindCubeFixed


def compute_pca(raw: WindCubeFixed, targets):
    var_of_velocity_over_time = _computute_var_over_time(
        raw.radial_velocity, raw.time, window_size=4 * 60
    )

    X = np.concatenate(
        (
            raw.cnr.reshape(-1, 1),
            raw.radial_velocity.reshape(-1, 1),
            raw.doppler_spectrum_width.reshape(-1, 1),
            var_of_velocity_over_time.reshape(-1, 1),
        ),
        axis=1,
    )

    X_scaled = StandardScaler().fit_transform(X)

    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    # Cluster 0
    x0 = -2.5
    y0 = 0.5
    dist0 = np.sqrt((X_pca[:, 0] - x0) ** 2 + (X_pca[:, 1] - y0) ** 2)

    # Cluster 1
    x1 = 1
    y1 = 3
    dist1 = np.sqrt((X_pca[:, 0] - x1) ** 2 + (X_pca[:, 1] - y1) ** 2)

    # Cluster 2 (half-plane)
    # ax+by+c = 0
    a = -6
    b = 1
    c = 2
    dist2 = (a * X_pca[:, 0] + b * X_pca[:, 1] + c) / np.sqrt(a**2 + b**2)

    n = 1
    fig, ax = db.plt.subplots(n, figsize=(25, n * 6))
    # cax = ax[0].scatter(X_pca[:, 0], X_pca[:, 1], s=1, alpha=0.1, c=targets.flatten())
    # fig.colorbar(cax, ax=ax[0])
    # x = np.linspace(0, 1, 10)
    # y = 6 * x - 2
    # ax[0].plot(x, y)

    ax.hexbin(X_pca[:, 0], X_pca[:, 1])

    db.add_fig(fig)
    db.plt.close("all")
    return (
        dist0.reshape(raw.cnr.shape),
        dist1.reshape(raw.cnr.shape),
        dist2.reshape(raw.cnr.shape),
    )


def compute_mask(raw: WindCubeFixed):
    var_velocity_time = _computute_var_over_time(
        raw.radial_velocity, raw.time, window_size=4 * 60
    )
    var_velocity_dist = _computute_var_over_distance(
        raw.radial_velocity, raw.radial_distance, window_size=400
    )
    var_cnr_time = _computute_var_over_time(raw.cnr, raw.time, window_size=5 * 60)
    abs_diff_diff_over_dist = _compute_abs_diff_diff(raw.radial_velocity, axis=1)
    abs_diff_diff_over_time = _compute_abs_diff_diff(raw.radial_velocity, axis=0)

    mask_cnr_coarse = _compute_cnr_mask(raw.cnr, th=-32)
    mask_var_velocity_over_time = var_velocity_time > 250
    mask_var_cnr_over_time = (np.exp(0.9) < var_cnr_time) & (var_cnr_time < np.exp(1.1))

    mask_cnr_var_vel_time = ((raw.cnr - (-32.5)) ** 2 / 5**2) + (
        (var_velocity_time - 350) ** 2 / 50**2
    )
    mask_pca_0, mask_pca_1, mask_pca_2 = compute_pca(
        raw, mask_var_velocity_over_time.astype(np.float64)
    )

    n = 6
    fig, ax = db.plt.subplots(n, figsize=(25, n * 5))
    i = 0
    # CNR
    cax = ax[i].imshow(
        raw.cnr.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        vmin=-35,
        vmax=-28,
    )
    fig.colorbar(cax, ax=ax[i])
    ax[i].set_title("cnr")

    # Doppler velocity
    i += 1
    cax = ax[i].imshow(
        raw.radial_velocity.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap="RdBu_r",
        vmin=-15,
        vmax=15,
    )
    fig.colorbar(cax, ax=ax[i])
    ax[i].set_title("radial_velocity")

    # Doppler spectrum width
    i += 1
    cax = ax[i].imshow(
        raw.doppler_spectrum_width.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
    )
    fig.colorbar(cax, ax=ax[i])
    ax[i].set_title("doppler spectrum width")

    ## CNR variance
    # i += 1
    # cax = ax[i].imshow(
    #    var_cnr_time.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    vmin=np.exp(0.75),
    #    vmax=np.exp(1.25),
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("var cnr over time")
    #### hist
    # i += 1
    # ax[i].hist(np.log(var_cnr_time + 1e-6).flatten(), bins=1000, range=(0, 5))
    # ax[i].set_title("var cnr over time")

    ## Doppler velocity variance over time
    # i += 1
    # cax = ax[i].imshow(
    #    var_velocity_time.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    vmin=200,
    #    vmax=400,
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("var radial_velocity over time")

    ## Doppler velocity variance over distance
    # i += 1
    # cax = ax[i].imshow(
    #    var_velocity_dist.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    vmin=200,
    #    vmax=400,
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("var radial_velocity over distance")

    ## Abs diff diff over dist
    # i += 1
    # cax = ax[i].imshow(
    #    abs_diff_diff_over_dist.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("abs diff diff over dist")
    ## Abs diff diff over time
    # i += 1
    # cax = ax[i].imshow(
    #    abs_diff_diff_over_time.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("abs diff diff over time")

    ## CNR vs velocity
    # i += 1
    # ax[i].hexbin(
    #    raw.cnr.flatten(),
    #    raw.radial_velocity.flatten(),
    # )
    # ax[i].set_title("cnr vs velocity")

    ## CNR vs spectrum widtgh
    # i += 1
    # ax[i].hexbin(raw.cnr.flatten(), raw.doppler_spectrum_width.flatten())
    # ax[i].set_title("cnr vs spectrum width")

    ## CNR vs var vel over time
    # i += 1
    # ax[i].hexbin(raw.cnr.flatten(), var_velocity_time.flatten())
    # ax[i].set_title("cnr vs var velocity over time")

    ## vel vs var vel over time
    # i += 1
    # ax[i].hexbin(
    #    raw.radial_velocity.flatten(),
    #    var_velocity_time.flatten(),
    #    norm=db.mpl.colors.LogNorm(),
    # )
    # ax[i].set_title("velocity vs var velocity over time")

    ## CNR vs var vel over dist
    # i += 1
    # ax[i].hexbin(raw.cnr.flatten(), var_velocity_dist.flatten())
    # ax[i].set_title("cnr vs var velocity over distance")

    ## CNR vs abs diff diff over time
    # i += 1
    # ax[i].hexbin(raw.cnr.flatten(), abs_diff_diff_over_time.flatten())
    # ax[i].set_title("cnr vs abs diff diff over time")

    ## CNR vs abs diff diff over dist
    # i += 1
    # ax[i].hexbin(raw.cnr.flatten(), abs_diff_diff_over_dist.flatten())
    # ax[i].set_title("cnr vs abs diff diff over dist")

    ## Coarse cnr mask
    # i += 1
    # cax = ax[i].imshow(
    #    mask_cnr_coarse.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    cmap="binary_r",
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("mask_cnr_coarse")

    ## Velocity variance over time mask
    # i += 1
    # cax = ax[i].imshow(
    #    mask_var_velocity_over_time.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    cmap="binary_r",
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("mask_var_velocity_over_time")

    ## CNR variance over time mask
    # i += 1
    # cax = ax[i].imshow(
    #    mask_var_cnr_over_time.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    cmap="binary_r",
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("mask_var_cnr_over_time")

    ## cnr var vel time mask
    # i += 1
    # cax = ax[i].imshow(
    #    mask_cnr_var_vel_time.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    cmap="binary_r",
    #    norm=db.mpl.colors.LogNorm(vmin=1, vmax=2),
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("mask_cnr_var_vel_time")

    ## cnr var vel time mask
    # i += 1
    # cax = ax[i].imshow(
    #    mask_cnr_var_vel_time.T < 1.5,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    cmap="binary_r",
    # )
    # fig.colorbar(cax, ax=ax[i])
    # ax[i].set_title("mask_cnr_var_vel_time")

    # PCA mask 0
    i += 1
    cax = ax[i].imshow(
        mask_pca_0.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap="binary_r",
    )
    fig.colorbar(cax, ax=ax[i])
    ax[i].set_title("mask_pca_0")

    # PCA mask 1
    i += 1
    cax = ax[i].imshow(
        mask_pca_1.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap="binary_r",
    )
    fig.colorbar(cax, ax=ax[i])
    ax[i].set_title("mask_pca_1")

    # PCA mask 2
    i += 1
    cax = ax[i].imshow(
        mask_pca_2.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap="binary_r",
    )
    fig.colorbar(cax, ax=ax[i])
    ax[i].set_title("mask_pca_2")

    db.plotutils.pretty_fig(fig)
    db.add_fig(fig)
    db.plt.close("all")
    breakpoint()
    pass


def _compute_cnr_mask(cnr, th):
    return cnr < th


def _computute_var_over_time(x, time, window_size):
    window_size_str = f"{window_size}s"
    df = pl.from_numpy(x)
    df = df.with_columns(pl.Series("dt", time))
    df_var = df.with_columns(
        pl.exclude("dt").rolling_var_by(
            "dt",
            window_size=window_size_str,
            closed="both",
            ddof=0,
        ),
    )
    var = df_var.select(pl.exclude("dt")).to_numpy()
    return var


def _computute_var_over_distance(x, distance, window_size):
    median_diff = np.median(np.diff(distance))
    window_size_steps = max(3, int(np.ceil(window_size / median_diff)))
    df = pl.from_numpy(x.T)
    df_var = df.with_columns(
        pl.exclude("dt").rolling_var(
            window_size=window_size_steps,
            center=True,
            min_periods=1,
            ddof=0,
        ),
    )
    var = df_var.to_numpy().T
    return var


def _compute_abs_diff_diff(x, axis):
    if axis == 0:
        zeros = np.zeros_like(x[0, :])[np.newaxis, :]
    elif axis == 1:
        zeros = np.zeros_like(x[:, 0])[:, np.newaxis]
    else:
        raise ValueError("Axis must be 0 or 1")
    add = np.concat(
        (zeros, np.abs(np.diff(np.diff(x, axis=axis), axis=axis)), zeros), axis=axis
    )
    return add
