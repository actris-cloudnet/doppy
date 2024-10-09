import pytest
from doppy import exceptions, options, product
from doppy.data.api import Api


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("warsaw", "2024-09-21", ""),
        ("chilbolton", "2024-09-29", ""),
        ("granada", "2023-07-07", ""),
        ("vehmasmaki", "2022-12-23", ""),
    ],
)
def test_tke(site, date, reason, cache):
    api = Api(cache=cache)
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
        and rec["filename"].startswith("VAD")
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_stare],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )
    wind = product.Wind.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl_wind],
    )
    pulses_per_ray = 10_000
    pulse_repetition_rate = 15e3  # 1/s
    integration_time = pulses_per_ray / pulse_repetition_rate
    beam_divergence = 33e-6  # radians
    _tke = product.TurbulentKineticEnergy.from_stare_and_wind(
        stare, wind, integration_time, beam_divergence
    )
    breakpoint()


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason,err",
    [
        ("lindenberg", "2024-07-26", "", exceptions.NoDataError),
        ("limassol", "2024-09-22", "", exceptions.NoDataError),
        ("bucharest", "2024-09-25", "", exceptions.NoDataError),
        ("punta-arenas", "2021-11-27", "", exceptions.NoDataError),
        ("mindelo", "2024-09-25", "", exceptions.NoDataError),
        ("hyytiala", "2024-04-07", "", exceptions.NoDataError),
        ("leipzig", "2024-09-28", "", exceptions.NoDataError),
        ("juelich", "2024-09-24", "", exceptions.NoDataError),
        ("kenttarova", "2023-12-09", "", exceptions.NoDataError),
        ("neumayer", "2024-09-20", "", exceptions.NoDataError),
        ("eriswil", "2024-03-03", "", exceptions.NoDataError),
        ("soverato", "2021-09-03", "", exceptions.NoDataError),
    ],
)
def test_tke_bad(site, date, reason, err, cache):
    api = Api(cache=cache)
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
        and rec["filename"].startswith("VAD")
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    with pytest.raises(err):
        stare = product.Stare.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl_stare],
            data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )
        wind = product.Wind.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl_wind],
        )
        pulses_per_ray = 10_000
        pulse_repetition_rate = 15e3  # 1/s
        integration_time = pulses_per_ray / pulse_repetition_rate
        beam_divergence = 33e-6  # radians
        _tke = product.turbulent_kinetic_energy.from_stare_and_wind(
            stare, wind, integration_time, beam_divergence
        )
