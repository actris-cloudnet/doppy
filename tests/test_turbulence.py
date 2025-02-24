import numpy as np
import pytest
from doppy.data.api import Api
from doppy.options import BgCorrectionMethod
from doppy.product.stare import Stare
from doppy.product.turbulence import HorizontalWind, Options, Turbulence, VerticalWind
from doppy.product.wind import Wind


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date",
    [
        ("bucharest", "2019-11-30"),
        ("bucharest", "2020-10-24"),
        ("bucharest", "2024-03-08"),
        ("bucharest", "2024-06-28"),
        ("bucharest", "2024-10-16"),
        ("chilbolton", "2017-11-29"),
        ("chilbolton", "2019-06-17"),
        ("chilbolton", "2021-02-07"),
        ("chilbolton", "2022-06-06"),
        ("chilbolton", "2022-06-27"),
        ("eriswil", "2023-01-07"),
        ("eriswil", "2023-11-28"),
        ("eriswil", "2023-12-23"),
        ("eriswil", "2024-01-10"),
        ("eriswil", "2024-02-27"),
        ("granada", "2019-05-23"),
        ("granada", "2021-09-10"),
        ("granada", "2021-12-09"),
        ("granada", "2022-09-10"),
        ("granada", "2023-06-16"),
        ("hyytiala", "2022-11-07"),
        ("hyytiala", "2023-07-06"),
        ("hyytiala", "2023-09-13"),
        ("hyytiala", "2023-12-12"),
        ("hyytiala", "2024-03-26"),
        ("juelich", "2023-05-04"),
        ("juelich", "2024-01-16"),
        ("juelich", "2024-04-11"),
        ("juelich", "2024-05-10"),
        ("juelich", "2024-11-26"),
        ("kenttarova", "2023-01-17"),
        ("kenttarova", "2023-05-29"),
        ("kenttarova", "2023-09-02"),
        ("kenttarova", "2023-10-04"),
        ("kenttarova", "2023-12-15"),
        ("leipzig", "2022-04-13"),
        ("leipzig", "2022-11-01"),
        ("leipzig", "2022-11-15"),
        ("leipzig", "2023-05-23"),
        ("leipzig", "2024-10-27"),
        ("lindenberg", "2024-05-06"),
        ("lindenberg", "2024-05-26"),
        ("lindenberg", "2024-06-22"),
        ("lindenberg", "2024-07-06"),
        ("lindenberg", "2024-11-08"),
        ("mindelo", "2023-02-08"),
        ("mindelo", "2023-11-05"),
        ("mindelo", "2024-05-14"),
        ("mindelo", "2024-10-10"),
        ("mindelo", "2024-10-27"),
        ("neumayer", "2024-01-13"),
        ("neumayer", "2024-01-28"),
        ("neumayer", "2024-02-15"),
        ("neumayer", "2024-03-03"),
        ("neumayer", "2024-04-16"),
        ("potenza", "2023-10-13"),
        ("punta-arenas", "2019-01-05"),
        ("punta-arenas", "2021-01-22"),
        ("punta-arenas", "2021-01-30"),
        ("punta-arenas", "2021-05-23"),
        ("punta-arenas", "2021-11-21"),
        ("soverato", "2021-06-27"),
        ("soverato", "2021-07-22"),
        # ("soverato", "2021-08-15"),
        # TODO: handle Stare files with multiple azimuth angles
        ("soverato", "2021-08-22"),
        ("soverato", "2021-08-26"),
        ("vehmasmaki", "2021-01-19"),
        ("vehmasmaki", "2022-04-03"),
        ("vehmasmaki", "2023-09-05"),
        ("vehmasmaki", "2023-12-24"),
        ("vehmasmaki", "2023-12-26"),
        ("warsaw", "2022-04-20"),
        ("warsaw", "2022-05-02"),
        ("warsaw", "2022-07-12"),
        ("warsaw", "2023-08-13"),
        ("warsaw", "2023-10-21"),
        ("warsaw", "2024-06-08"),
    ],
)
def test(site, date):
    api = Api(cache=True)
    stare, wind = _get_stare_and_wind(api, site, date)

    Turbulence.from_winds(
        VerticalWind(
            time=stare.time,
            height=stare.radial_distance,
            w=stare.radial_velocity,
            mask=stare.mask_radial_velocity,
        ),
        HorizontalWind(
            time=wind.time,
            height=wind.height,
            V=np.sqrt(wind.zonal_wind**2 + wind.meridional_wind**2),
        ),
        Options(ray_accumulation_time=1),
    )


def _get_stare_and_wind(api, site, date):
    records = api.get_raw_records(site, date)
    records_hpl_stare = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and "cross" not in set(rec["tags"])
        and rec["filename"].startswith("Stare")
    ]
    records_hpl_wind = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl")
        and "cross" not in set(rec["tags"])
        and not rec["filename"].startswith("Stare")
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_stare],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=BgCorrectionMethod.FIT,
    )
    wind = Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_wind],
    )
    return stare, wind
