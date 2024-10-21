
    @classmethod
    def from_windcube_data(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
    ) -> Stare:
        raws = doppy.raw.WindCubeFixed.from_srcs(data)
        raw = doppy.raw.WindCubeFixed.merge(raws)
        mask = _compute_mask_for_windcube(raw)
        return
        fig, ax = db.plt.subplots()
        ax.imshow(
            raw.relative_beta.T,
            origin="lower",
            aspect="auto",
            interpolation="none",
            norm=db.mpl.colors.LogNorm(vmin=1e-9, vmax=1e-7),
        )
        db.add_fig(fig)
        fig, ax = db.plt.subplots()
        ax.imshow(
            raw.radial_velocity.T,
            origin="lower",
            aspect="auto",
            interpolation="none",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
        )
        db.add_fig(fig)
        fig, ax = db.plt.subplots()
        v_masked = raw.radial_velocity.copy()
        v_masked[raw.radial_velocity_confidence < 99] = np.nan
        ax.imshow(
            v_masked.T,
            origin="lower",
            aspect="auto",
            interpolation="none",
            cmap="RdBu_r",
            vmin=-1,
            vmax=1,
        )
        db.add_fig(fig)
        print(db.describe(raw.radial_velocity))
        print(db.describe(raw.radial_velocity[raw.radial_velocity_confidence == 100]))

def _compute_sliding_var_over_time(velocity, time):
    df = pl.from_numpy(velocity)
    df = df.with_columns(pl.Series("dt", time))
    df_var = df.with_columns(
        pl.exclude("dt").rolling_var_by(
            "dt",
            window_size="5m",
            closed="both",
            ddof=0,
        ),
    )
    var = df_var.select(pl.exclude("dt")).to_numpy()
    return var


def _compute_sliding_mean_over_radial_distance(
    velocity, radial_distance, window_distance
):
    # window_distance in meters
    median_diff = np.median(np.diff(radial_distance))
    window_size = max(3, int(np.ceil(window_distance / median_diff)))
    df = pl.from_numpy(velocity.T)
    df_mean = df.with_columns(
        pl.exclude("dt").rolling_mean(
            window_size=window_size,
            min_periods=1,
        ),
    )
    mean = df_mean.to_numpy().T
    # fig, ax = db.plt.subplots()

    # ax.imshow(
    #    mean.T,
    #    origin="lower",
    #    aspect="auto",
    #    interpolation="none",
    #    cmap="RdBu_r",
    #    vmin=-10,
    #    vmax=10,
    # )
    # db.add_fig(fig)
    return mean


def _compute_sliding_var_over_radial_distance(
    velocity, radial_distance, window_distance
):
    # window_distance in meters
    median_diff = np.median(np.diff(radial_distance))
    window_size = max(3, int(np.ceil(window_distance / median_diff)))
    df = pl.from_numpy(velocity.T)
    df_var = df.with_columns(
        pl.exclude("dt").rolling_var(
            window_size=window_size,
            center=True,
            min_periods=1,
            ddof=0,
        ),
    )
    var = df_var.to_numpy().T
    return var


def _filt(arr):
    i = len(arr) / 2
    arr_wo = np.delete(arr, i)
    if all(np.isnan(arr_wo)):
        return True
    return False


def _compute_mask_for_windcube(raw: WindCubeFixed):
    # print(db.describe(raw.cnr))
    # mask_cnr =  raw.cnr < -27

    mask_cnr = raw.cnr < -30
    var_over_time = _compute_sliding_var_over_time(raw.radial_velocity, raw.time)
    var_over_radial_distance = _compute_sliding_var_over_radial_distance(
        raw.radial_velocity, raw.radial_distance, 400
    )
    mean_over_radial_distance = _compute_sliding_mean_over_radial_distance(
        raw.radial_velocity, raw.radial_distance, 1000
    )
    med_over_window = scipy.ndimage.median_filter(raw.radial_velocity, size=5)
    med_absdiff = np.abs(raw.radial_velocity - med_over_window)
    denominator = np.maximum(np.abs(med_over_window), np.finfo(np.float64).eps)
    med_rel = med_absdiff / denominator

    # mask_var_t = var_over_time > 225
    mask_var_t = var_over_time > 200
    # mask_var_r = var_over_radial_distance > 50
    mask_med = med_absdiff > 10
    mask_med_rel = med_rel > 100

    print(db.describe(med_rel))
    mask = mask_cnr | mask_var_t | mask_med  # | mask_med_rel

    # remove specles
    v = raw.radial_velocity.copy()
    v[mask] = mean_over_radial_distance[mask]
    zeros = np.zeros_like(v[:, 0])[:, np.newaxis]
    vdiff = np.concat((zeros, np.diff(np.diff(v, axis=1), axis=1), zeros), axis=1)
    vdiff_mask = np.abs(vdiff) > 5

    mask = mask | vdiff_mask

    # Dont mask if signal is strong enough
    mask = mask & (raw.cnr < -24)

    nplots = 12
    width = 10
    height = 3
    fig, ax = db.plt.subplots(nplots, figsize=(width, nplots * height))

    ## CNR
    ax[0].imshow(
        raw.cnr.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        # norm=db.mpl.colors.SymLogNorm(linthresh=0.1,vmin=0.1*raw.cnr.min(), vmax=0.1*raw.cnr.max()),
        vmin=-35,
        vmax=-25,
    )
    x = raw.cnr.copy()
    x[mask] = np.nan
    ax[1].imshow(
        x.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        # norm=db.mpl.colors.SymLogNorm(linthresh=0.1,vmin=0.1*raw.cnr.min(), vmax=0.1*raw.cnr.max()),
        vmin=-35,
        vmax=-25,
    )

    ## Radial velocity
    ax[2].imshow(
        raw.radial_velocity.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap="RdBu_r",
        vmin=-10,
        vmax=10,
    )

    x = raw.radial_velocity.copy()
    x[mask] = np.nan
    v = raw.radial_velocity.copy()
    v[mask] = mean_over_radial_distance[mask]
    #
    vdiff = np.concat(
        (np.zeros_like(v[:, :2]), np.diff(np.diff(v, axis=1), axis=1)), axis=1
    )
    # ax[3].hist(np.abs(vdiff).flatten(),bins=1000)
    vdiff_mask = np.abs(vdiff) > 20
    ax[3].imshow(
        x.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        cmap="RdBu_r",
        vmin=-10,
        vmax=10,
    )

    ## Beta
    ax[4].imshow(
        raw.relative_beta.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        norm=db.mpl.colors.LogNorm(vmin=1e-9, vmax=1e-7),
    )
    x = raw.relative_beta.copy()
    x[mask] = np.nan
    ax[5].imshow(
        x.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        norm=db.mpl.colors.LogNorm(vmin=1e-9, vmax=1e-7),
    )

    # Plot masks
    ax[6].imshow(
        mask_cnr.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
    )

    ax[7].imshow(
        mask_var_t.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
    )
    ax[8].imshow(
        mask.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
    )

    ax[9].imshow(
        med_over_window.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
    )

    ax[10].imshow(
        mask_med.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
    )

    ax[11].imshow(
        med_rel.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        norm=db.mpl.colors.LogNorm(vmin=1e-1, vmax=1e3),
    )

    # ax[11].hist(
    #    var_over_radial_distance[var_over_radial_distance > 10].flatten(), bins=1000
    # )

    db.add_fig(fig)
