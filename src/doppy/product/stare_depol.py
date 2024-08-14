import numpy as np
import numpy.typing as npt

from doppy.product.stare import Stare


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
    """

    time: npt.NDArray[np.datetime64]
    radial_distance: npt.NDArray[np.float64]
    elevation: npt.NDArray[np.float64]
    beta: npt.NDArray[np.float64]
    radial_velocity: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]
    depolarisation: npt.NDArray[np.float64]
    wavelength: float
    system_id: str

    def __init__(self, co: Stare, cross: Stare):
        if co.wavelength != cross.wavelength:
            raise ValueError(
                "Different wavelength in co and cross: "
                f"{co.wavelength} vs {cross.wavelength}"
            )
        if co.system_id != cross.system_id:
            raise ValueError(
                "Different system ID in co and cross: "
                f"{co.system_id} vs {cross.system_id}"
            )
        if not np.allclose(co.radial_distance, cross.radial_distance):
            raise ValueError("Different radial distance in co and cross")

        time_ind = np.argmin(np.abs(co.time - cross.time[:, np.newaxis]), axis=0)
        cross_elevation = cross.elevation[time_ind]
        cross_beta = cross.beta[time_ind, :]

        if not np.allclose(co.elevation, cross_elevation):
            raise ValueError("Different elevation in co and cross")

        self.time = co.time
        self.radial_distance = co.radial_distance
        self.elevation = co.elevation
        self.beta = co.beta
        self.radial_velocity = co.radial_velocity
        self.mask = co.mask
        self.depolarisation = cross_beta / co.beta
        self.wavelength = co.wavelength
        self.system_id = co.system_id
