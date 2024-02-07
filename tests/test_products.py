import doppy.netcdf
import pytest
from doppy import exceptions, options, product
from doppy.data.api import Api


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("bucharest", "2021-02-18", ""),
        ("bucharest", "2021-02-17", ""),
        ("bucharest", "2021-02-16", ""),
        ("chilbolton", "2023-11-01", ""),
        ("eriswil", "2023-11-30", ""),
        ("granada", "2023-07-17", ""),
        ("hyytiala", "2023-09-20", ""),
        ("juelich", "2023-11-01", ""),
        ("kenttarova", "2023-11-01", ""),
        ("leipzig", "2023-10-12", ""),
        # ("lindenberg", "2023-11-01", ""),
        ("mindelo", "2023-11-01", ""),
        ("mindelo", "2023-11-02", ""),
        ("mindelo", "2023-11-03", ""),
        ("potenza", "2023-10-28", ""),
        ("punta-arenas", "2021-11-29", ""),
        ("soverato", "2021-09-06", ""),
        ("vehmasmaki", "2022-12-30", ""),
        ("warsaw", "2023-11-01", ""),
        ("hyytiala", "2024-01-29", "some files have problems => skip them"),
    ],
)
def test_stare(site, date, reason):
    api = Api()
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    _stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,err,reason",
    [
        ("warsaw", "2024-02-03", exceptions.NoDataError, "Missing bg files"),
        ("neumayer", "2024-02-02",exceptions.NoDataError, "No data with elevation angle 90"),
    ],
)
def test_bad_stare(site, date, err, reason):
    api = Api()
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]

    with pytest.raises(err):
        _stare = product.Stare.from_halo_data(
            data=[api.get_record_content(r) for r in records_hpl],
            data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
            bg_correction_method=options.BgCorrectionMethod.FIT,
        )


@pytest.mark.slow
@pytest.mark.parametrize(
    "site,date,reason",
    [
        ("warsaw", "2023-11-01", ""),
    ],
)
def test_netcdf_writing(site, date, reason):
    api = Api()
    records = api.get_raw_records(site, date)
    records_hpl = [
        rec
        for rec in records
        if rec["filename"].endswith(".hpl") and "cross" not in set(rec["tags"])
    ]
    records_bg = [rec for rec in records if rec["filename"].startswith("Background")]
    stare = product.Stare.from_halo_data(
        data=[api.get_record_content(r) for r in records_hpl],
        data_bg=[(api.get_record_content(r), r["filename"]) for r in records_bg],
        bg_correction_method=options.BgCorrectionMethod.FIT,
    )

    _nc_buf = (
        doppy.netcdf.Dataset()
        .add_dimension("time")
        .add_dimension("range")
        .add_time(
            name="time",
            dimensions=("time",),
            standard_name="time",
            long_name="Time UTC",
            data=stare.time,
            dtype="f8",
        )
        .add_variable(
            name="range",
            dimensions=("range",),
            units="m",
            data=stare.radial_distance,
            dtype="f4",
        )
        .add_variable(
            name="elevation",
            dimensions=("time",),
            units="degrees",
            data=stare.elevation,
            dtype="f4",
            long_name="elevation from horizontal",
        )
        .add_variable(
            name="beta_raw",
            dimensions=("time", "range"),
            units="sr-1 m-1",
            data=stare.beta,
            dtype="f4",
        )
        .add_variable(
            name="beta",
            dimensions=("time", "range"),
            units="sr-1 m-1",
            data=stare.beta,
            dtype="f4",
            mask=stare.mask,
        )
        .add_variable(
            name="v",
            dimensions=("time", "range"),
            units="m s-1",
            long_name="Doppler velocity",
            data=stare.radial_velocity,
            dtype="f4",
            mask=stare.mask,
        )
        .add_scalar_variable(
            name="wavelength",
            units="m",
            standard_name="radiation_wavelength",
            data=stare.wavelength,
            dtype="f4",
        )
    ).close()
