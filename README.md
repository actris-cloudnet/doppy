# Doppy – Doppler wind lidar processing

[![CI](https://github.com/actris-cloudnet/doppy/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/doppy/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/doppy.svg)](https://badge.fury.io/py/doppy)

## Products

- Stare: [src](https://github.com/actris-cloudnet/doppy/blob/main/src/doppy/product/stare.py), [Cloudnet examples](https://cloudnet.fmi.fi/search/visualizations?experimental=true&product=doppler-lidar&dateFrom=2024-06-05&dateTo=2024-06-05)
- Wind: [src](https://github.com/actris-cloudnet/doppy/blob/main/src/doppy/product/wind.py), [Cloudnet examples](https://cloudnet.fmi.fi/search/visualizations?experimental=true&product=doppler-lidar-wind&dateFrom=2024-06-05&dateTo=2024-06-05)

## Instruments

- HALO Photonics Streamline lidars (stare, wind)
- Leosphere WindCube WLS200S (wind)
- Leosphere WindCube WLS70 (wind)

## Install

```sh
pip install doppy
```

## Usage

### Stare

```python
import doppy

stare = doppy.product.Stare.from_halo_data(
    data=LIST_OF_STARE_FILE_PATHS,
    data_bg=LIST_OF_BACKGROUND_FILE_PATHS,
    bg_correction_method=doppy.options.BgCorrectionMethod.FIT,
)

stare.write_to_netcdf(FILENAME)
```

### Stare with depolarisation

```python
import doppy

stare_depol = doppy.product.StareDepol.from_halo_data(
    co_data=LIST_OF_STARE_CO_FILE_PATHS,
    co_data_bg=LIST_OF_BACKGROUND_CO_FILE_PATHS,
    cross_data=LIST_OF_STARE_CROSS_FILE_PATHS,
    cross_data_bg=LIST_OF_BACKGROUND_CROSS_FILE_PATHS,
    bg_correction_method=doppy.options.BgCorrectionMethod.FIT,
    polariser_bleed_through=0,
)

stare_depol.write_to_netcdf(FILENAME)
```

### Wind

```python
import doppy

wind = doppy.product.Wind.from_halo_data(
    data=LIST_OF_WIND_SCAN_HPL_FILES,
)

# You can also pass instrument azimuth offset in degrees as an option
wind = doppy.product.Wind.from_halo_data(
    data=LIST_OF_WIND_SCAN_HPL_FILES,
    options=doppy.product.wind.Options(azimuth_offset_deg=30),
)

# For windcube wls200s use
wind = doppy.product.Wind.from_windcube_data(
    data=LIST_OF_VAD_NETCDF_FILES,
)

# For windcube wls70 use
wind = doppy.product.Wind.from_wls70_data(
    data=LIST_OF_RTD_FILES,
)

wind.write_to_netcdf(FILENAME)
```

### Raw files

```python
import doppy

# Halo
raws_hpl = doppy.raw.HaloHpl.from_srcs(LIST_OF_HPL_FILES)
raws_bg = doppy.raw.HaloBg.from_srcs(LIST_OF_BACKGROUND_FILES)
raw_system_params = doppy.raw.HaloSysParams.from_src(SYSTEM_PARAMS_FILENAME)

# Windcube WLS200S
raws_wls200s = doppy.raw.WindCube.from_vad_or_dbs_srcs(LIST_OF_VAD_NETCDF_FILES)

# Windcube WLS70
raws_wls70 = doppy.raw.Wls70.from_srcs(LIST_OF_RTD_FILES)
```
