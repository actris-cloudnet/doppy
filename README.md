# Doppy – Doppler wind lidar processing

[![CI](https://github.com/actris-cloudnet/doppy/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/doppy/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/doppy.svg)](https://badge.fury.io/py/doppy)

## Products

- [Stare](https://github.com/actris-cloudnet/doppy/blob/main/src/doppy/product/stare.py): [Examples](https://cloudnet.fmi.fi/search/visualizations?experimental=true&product=doppler-lidar&dateFrom=2024-06-05&dateTo=2024-06-05)
- [Wind](https://github.com/actris-cloudnet/doppy/blob/main/src/doppy/product/wind.py): [Examples](https://cloudnet.fmi.fi/search/visualizations?experimental=true&product=doppler-lidar-wind&dateFrom=2024-06-05&dateTo=2024-06-05)

## Instruments

- HALO Photonics Streamline lidars (stare, wind)
- Leosphere WindCube WLS200S (wind)
- Leosphere WindCube WLS70 (wind)

## Install

```sh
pip install doppy
```

## Usage

```python
import doppy

stare = doppy.product.Stare.from_halo_data(
    data=LIST_OF_STARE_FILE_PATHS,
    data_bg=LIST_OF_BACKGROUND_FILE_PATHS,
    bg_correction_method=doppy.options.BgCorrectionMethod.FIT,
)


(
    doppy.netcdf.Dataset(FILENAME)
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
    .add_attribute("serial_number", stare.system_id)
    .add_attribute("doppy_version", doppy.__version__)
).close()

```
