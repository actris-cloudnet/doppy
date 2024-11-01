import argparse
import hashlib
import pathlib
import pickle

import devboard as db
import doppy
from doppy.data.api import Api


def main(args):
    api = Api(cache=True)
    stare = _get_stare(args, api)
    wind = _get_wind(args, api)
    tke = _get_tke(args, stare, wind)
    _plot_tke(tke, args)


def _plot_tke(tke, args):
    # db.mpl.rcParams["font.family"] = "IBM Plex Mono"
    db.mpl.rcParams["font.family"] = "Metropolis"
    db.mpl.rcParams["font.size"] = 16
    aspect = 10 / 3
    width = 25
    height = width / aspect
    fig, ax = db.plt.subplots(figsize=(width, height))
    hm = tke.height < 2050
    ax.imshow(
        tke.dissipation_rate[:, hm].T,
        origin="lower",
        aspect="auto",
        norm=db.mpl.colors.LogNorm(vmin=1e-7, vmax=1e-1),
        cmap="inferno",
        extent=[tke.time[0], tke.time[-1], tke.height[hm][0], tke.height[hm][-1]],
        zorder=1,
    )
    ax.set_ylabel("Height (m)", rotation=0, horizontalalignment="right")
    ax.yaxis.set_label_coords(0, 1.04)

    ax.spines["bottom"].set_position(("outward", 10))
    ax.spines["left"].set_position(("outward", 10))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_axisbelow(True)
    # ax.yaxis.grid(True, color="white")
    # ax.xaxis.grid(True, color="white", linewidth=4)
    grid_color = "#dedede"
    # ax.xaxis.grid(True, color=grid_color, linewidth=2)
    # ax.yaxis.grid(True, color=grid_color, linewidth=2)
    # ax.set_facecolor("#f5f5f5")
    # ax.set_facecolor("#f0f0f0")
    ax.set_facecolor("#ffffff")
    ax.xaxis_date()
    ax.xaxis.set_major_locator(db.mpl.dates.AutoDateLocator())
    ax.xaxis.set_major_formatter(
        db.mpl.dates.ConciseDateFormatter(db.mpl.dates.AutoDateLocator())
    )
    site = args.site.capitalize()
    ax.set_title(f"Turbulent kinetic energy dissipation rate, {site}")

    db.add_fig(fig)

    output_path = "tke_plot.png"
    fig.savefig(output_path, dpi=400, bbox_inches="tight", format="png")


def _compute_hash(args):
    args_str = str(sorted(vars(args).items()))
    return hashlib.sha256(args_str.encode("utf-8")).hexdigest()


def _get_tke(args, stare, wind):
    hash = _compute_hash(args)
    cached_path = pathlib.Path("cache", hash, "tke.pickle")
    if cached_path.is_file():
        with cached_path.open("rb") as f:
            print(f"using cached tke: {cached_path}")
            tke = pickle.load(f)
            return tke
    pulses_per_ray = 10_000
    pulse_repetition_rate = 15e3  # 1/s
    integration_time = pulses_per_ray / pulse_repetition_rate
    beam_divergence = 33e-6  # radians
    tke = doppy.product.TurbulentKineticEnergy.from_stare_and_wind(
        stare, wind, integration_time, beam_divergence
    )
    cached_path.parent.mkdir(parents=True, exist_ok=True)
    with cached_path.open("wb") as f:
        pickle.dump(tke, f)
    return tke


def _get_stare(args, api):
    hash = _compute_hash(args)
    cached_path = pathlib.Path("cache", hash, "stare.pickle")
    if cached_path.is_file():
        with cached_path.open("rb") as f:
            stare = pickle.load(f)
            return stare
    records = api.get(
        "raw-files",
        {
            "site": args.site,
            "dateFrom": args.date_from,
            "dateTo": args.date_to,
            "instrumentPid": args.pid,
        },
    )
    records_hpl_stare = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and "cross" not in set(rec["tags"])
        and rec["filename"].startswith("Stare")
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = doppy.product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_stare],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=doppy.options.BgCorrectionMethod.FIT,
    )
    cached_path.parent.mkdir(parents=True, exist_ok=True)
    with cached_path.open("wb") as f:
        pickle.dump(stare, f)
    return stare


def _get_wind(args, api):
    hash = _compute_hash(args)
    cached_path = pathlib.Path("cache", hash, "wind.pickle")

    # If cached wind data exists, load it
    if cached_path.is_file():
        with cached_path.open("rb") as f:
            wind = pickle.load(f)
            return wind

    # Otherwise, fetch and compute wind data
    records = api.get(
        "raw-files",
        {
            "site": args.site,
            "dateFrom": args.date_from,
            "dateTo": args.date_to,
            "instrumentPid": args.pid,
        },
    )

    records_hpl_wind = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and "cross" not in set(rec["tags"])
        and rec["filename"].startswith("VAD")
    ]

    wind = doppy.product.Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_wind],
    )

    # Save computed wind data to cache
    cached_path.parent.mkdir(parents=True, exist_ok=True)
    with cached_path.open("wb") as f:
        pickle.dump(wind, f)

    return wind


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=str)
    parser.add_argument("--date", action=DateRangeAction, nargs="+")
    parser.add_argument("--pid", type=str)
    return parser.parse_args()


class DateRangeAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 1:
            # One date was provided; `date_from` and `date_to` are the same
            namespace.date_from = values[0]
            namespace.date_to = values[0]
        elif len(values) == 2:
            # Two dates were provided; map them to `date_from` and `date_to`
            namespace.date_from = values[0]
            namespace.date_to = values[1]
        else:
            parser.error(
                f"{option_string} expects at most 2 arguments; got {len(values)}."
            )


if __name__ == "__main__":
    args = _parse_args()
    main(args)
