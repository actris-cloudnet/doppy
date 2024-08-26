from __future__ import annotations

from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt

import doppy
from doppy import options
from doppy.product.stare import Stare


@dataclass
class StareDepol:
    """
    Stare product with depolarisation ratio derived from co-polarised and
    cross-polarised stare data.

    Attributes:
    -----------
    time
        An array of datetime64 objects representing the observation times.
    radial_distance
        An array of radial distances from the observation point, in meters.
    elevation
        An array of elevation angles corresponding to the observation points, in
        degrees.
    beta
        An array of backscatter coefficients for the co-polarised signal, in
        sr-1 m-1.
    beta_cross
        An array of backscatter coefficients for the cross-polarised signal, in
        sr-1 m-1.
    radial_velocity
        An array of radial velocities of the co-polarised signal, in m s-1.
    mask
        A boolean array indicating signal (True) or noise (False) data points.
    depolarisation
        An array of depolarisation ratios calculated as the ratio of
        co-polarised to cross-polarised backscatter coefficients.
    wavelength
        The wavelength of the lidar, in meters.
    system_id
        A string identifier for the lidar.


    Raises
    ------
    ValueError
        If the input `co` and `cross` products have mismatched wavelengths,
        system IDs, radial distances, or elevation angles, this exception is
        raised.


    References
    ----------
    Aerosol particle depolarization ratio at 1565 nm measured with a Halo Doppler lidar
        authors: Ville Vakkari, Holger Baars, Stephanie Bohlmann, Johannes Bühl,
            Mika Komppula, Rodanthi-Elisavet Mamouri, and Ewan James O'Connor
        doi: https://doi.org/10.5194/acp-21-5807-2021
    """

    time: npt.NDArray[np.datetime64]
    radial_distance: npt.NDArray[np.float64]
    elevation: npt.NDArray[np.float64]
    beta: npt.NDArray[np.float64]
    beta_cross: npt.NDArray[np.float64]
    radial_velocity: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]
    depolarisation: npt.NDArray[np.float64]
    polariser_bleed_through: float
    wavelength: float
    system_id: str

    def __init__(
        self,
        co: Stare,
        cross: Stare,
        polariser_bleed_through: float = 0.0,
    ):
        """
        Parameters
        ----------
        co: Stare
            The co-polarised data.
        cross: Stare
            The cross-polarised data. The `cross.time` array is expected to be sorted.
        polariser_bleed_through: float, default=0.0
            The amount of bleed-through from the polariser.
        """

        if co.beta.shape[1] != cross.beta.shape[1]:
            raise doppy.exceptions.ShapeError(
                "Range dimension mismatch in co and cross: "
                f"{co.beta.shape[1]} vs {cross.beta.shape[1]}"
            )

        if not np.isclose(co.wavelength, cross.wavelength):
            raise ValueError(
                "Different wavelength in co and cross: "
                f"{co.wavelength} vs {cross.wavelength}"
            )
        if co.system_id != cross.system_id:
            raise ValueError(
                "Different system ID in co and cross: "
                f"{co.system_id} vs {cross.system_id}"
            )
        if not np.allclose(co.radial_distance, cross.radial_distance, atol=1):
            raise ValueError("Different radial distance in co and cross")

        ind = np.searchsorted(cross.time, co.time, side="left")
        pick_ind = ind < len(cross.time)
        time_diff_threshold = 2 * np.median(np.diff(co.time))
        co_cross_timediff_below_threshold = (
            cross.time[ind[pick_ind]] - co.time[pick_ind] < time_diff_threshold
        )
        pick_ind[pick_ind] &= co_cross_timediff_below_threshold

        if not np.allclose(
            co.elevation[pick_ind], cross.elevation[ind[pick_ind]], atol=1
        ):
            raise ValueError("Different elevation in co and cross")

        depolarisation = np.full_like(co.beta, np.nan)
        co_beta = co.beta[pick_ind]
        depolarisation[pick_ind] = (
            cross.beta[ind[pick_ind]] - polariser_bleed_through * co_beta
        ) / co_beta
        cross_beta = np.full_like(co.beta, np.nan)
        cross_beta[pick_ind] = cross.beta[ind[pick_ind]]

        self.time = co.time
        self.radial_distance = co.radial_distance
        self.elevation = co.elevation
        self.beta = co.beta
        self.beta_cross = cross_beta
        self.radial_velocity = co.radial_velocity
        self.mask = co.mask
        self.depolarisation = depolarisation
        self.polariser_bleed_through = polariser_bleed_through
        self.wavelength = co.wavelength
        self.system_id = co.system_id

    @property
    def mask_depolarisation(self) -> npt.NDArray[np.bool_]:
        return np.isnan(self.depolarisation)

    @property
    def mask_beta_cross(self) -> npt.NDArray[np.bool_]:
        return np.isnan(self.beta_cross)

    @classmethod
    def from_halo_data(
        cls,
        co_data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
        co_data_bg: Sequence[str]
        | Sequence[Path]
        | Sequence[tuple[bytes, str]]
        | Sequence[tuple[BufferedIOBase, str]],
        cross_data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
        cross_data_bg: Sequence[str]
        | Sequence[Path]
        | Sequence[tuple[bytes, str]]
        | Sequence[tuple[BufferedIOBase, str]],
        bg_correction_method: options.BgCorrectionMethod,
        polariser_bleed_through: float = 0,
    ) -> StareDepol:
        co = Stare.from_halo_data(
            data=co_data, data_bg=co_data_bg, bg_correction_method=bg_correction_method
        )
        cross = Stare.from_halo_data(
            data=cross_data,
            data_bg=cross_data_bg,
            bg_correction_method=bg_correction_method,
        )
        return cls(co, cross, polariser_bleed_through)

    def write_to_netcdf(self, filename: str | Path) -> None:
        with doppy.netcdf.Dataset(filename) as nc:
            nc.add_dimension("time")
            nc.add_dimension("range")
            nc.add_time(
                name="time",
                dimensions=("time",),
                standard_name="time",
                long_name="Time UTC",
                data=self.time,
                dtype="f8",
            )
            nc.add_variable(
                name="range",
                dimensions=("range",),
                units="m",
                data=self.radial_distance,
                dtype="f4",
            )
            nc.add_variable(
                name="elevation",
                dimensions=("time",),
                units="degrees",
                data=self.elevation,
                dtype="f4",
                long_name="elevation from horizontal",
            )
            nc.add_variable(
                name="beta_raw",
                dimensions=("time", "range"),
                units="sr-1 m-1",
                data=self.beta,
                dtype="f4",
            )
            nc.add_variable(
                name="beta",
                dimensions=("time", "range"),
                units="sr-1 m-1",
                data=self.beta,
                dtype="f4",
                mask=self.mask,
            )
            nc.add_variable(
                name="v",
                dimensions=("time", "range"),
                units="m s-1",
                long_name="Doppler velocity",
                data=self.radial_velocity,
                dtype="f4",
                mask=self.mask,
            )
            nc.add_scalar_variable(
                name="wavelength",
                units="m",
                standard_name="radiation_wavelength",
                data=self.wavelength,
                dtype="f4",
            )
            nc.add_variable(
                name="depolarisation_raw",
                dimensions=("time", "range"),
                units="1",
                data=self.depolarisation,
                dtype="f4",
                mask=self.mask_depolarisation,
            )
            nc.add_variable(
                name="depolarisation",
                dimensions=("time", "range"),
                units="1",
                data=self.depolarisation,
                dtype="f4",
                mask=self.mask | self.mask_depolarisation,
            )
            nc.add_variable(
                name="beta_cross_raw",
                dimensions=("time", "range"),
                units="sr-1 m-1",
                data=self.beta_cross,
                mask=self.mask_beta_cross,
                dtype="f4",
            )
            nc.add_variable(
                name="beta_cross",
                dimensions=("time", "range"),
                units="sr-1 m-1",
                data=self.beta_cross,
                mask=self.mask | self.mask_beta_cross,
                dtype="f4",
            )
            nc.add_scalar_variable(
                name="polariser_bleed_through",
                units="1",
                long_name="Polariser bleed-through",
                data=self.polariser_bleed_through,
                dtype="f4",
            )
            nc.add_attribute("serial_number", self.system_id)
            nc.add_attribute("doppy_version", doppy.__version__)
