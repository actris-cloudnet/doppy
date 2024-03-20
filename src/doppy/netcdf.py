from __future__ import annotations

from typing import Literal, TypeAlias

import netCDF4
import numpy as np
import numpy.typing as npt

NetCDFDataType: TypeAlias = Literal["f4", "f8", "i4", "i8", "u4", "u8"]


class Dataset:
    def __init__(self, filename: str) -> None:
        self.nc = netCDF4.Dataset(filename, mode="w")

    def add_dimension(self, dim: str) -> Dataset:
        self.nc.createDimension(dim, None)
        return self

    def add_atribute(self, key: str, val: str) -> Dataset:
        setattr(self.nc, key, val)
        return self

    def add_time(
        self,
        name: str,
        dimensions: tuple[str, ...],
        data: npt.NDArray[np.datetime64],
        dtype: NetCDFDataType,
        standard_name: str | None = None,
        long_name: str | None = None,
    ) -> Dataset:
        time, units, calendar = _convert_time(data)
        var = self.nc.createVariable(name, dtype, dimensions, compression="zlib")
        var.units = units
        var.calendar = calendar
        var[:] = time
        if standard_name is not None:
            var.standard_name = standard_name
        if long_name is not None:
            var.long_name = long_name
        return self

    def add_variable(
        self,
        name: str,
        dimensions: tuple[str, ...],
        units: str,
        data: npt.NDArray[np.float64],
        dtype: NetCDFDataType,
        standard_name: str | None = None,
        long_name: str | None = None,
        mask: npt.NDArray[np.bool_] | None = None,
    ) -> Dataset:
        fill_value = netCDF4.default_fillvals[dtype] if mask is not None else None
        var = self.nc.createVariable(
            name, dtype, dimensions, fill_value=fill_value, compression="zlib"
        )
        var.units = units
        if mask is not None:
            var[:] = np.ma.masked_array(data, mask)  # type: ignore
        else:
            var[:] = data
        if standard_name is not None:
            var.standard_name = standard_name
        if long_name is not None:
            var.long_name = long_name
        return self

    def add_scalar_variable(
        self,
        name: str,
        units: str,
        data: np.float64 | np.int64 | float | int,
        dtype: NetCDFDataType,
        standard_name: str | None = None,
        long_name: str | None = None,
        mask: npt.NDArray[np.bool_] | None = None,
    ) -> Dataset:
        var = self.nc.createVariable(name, dtype)
        var.units = units
        var[:] = data
        if standard_name is not None:
            var.standard_name = standard_name
        if long_name is not None:
            var.long_name = long_name
        return self

    def close(self) -> None:
        self.nc.close()


def _convert_time(
    time: npt.NDArray[np.datetime64],
) -> tuple[npt.NDArray[np.float64], str, str]:
    """
    Parameters
    ----------
    time : npt.NDArray[np.datetime64["us"]]
        Must be represented in UTC
    """
    if time.dtype != "<M8[us]":
        raise TypeError("time must be datetime64[us]")
    MICROSECONDS_TO_HOURS = 1 / (1e6 * 3600)
    start_of_day = time.min().astype("datetime64[D]")
    hours_since_start_of_day = (time - start_of_day).astype(
        np.float64
    ) * MICROSECONDS_TO_HOURS
    units = f"hours since {np.datetime_as_string(start_of_day)} 00:00:00 +00:00"
    calendar = "standard"
    return hours_since_start_of_day, units, calendar
