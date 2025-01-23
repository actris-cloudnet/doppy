from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class ModelWind:
    time: npt.NDArray[np.datetime64]
    height: npt.NDArray[np.float64] # Above ground level
    zonal_wind: npt.NDArray[np.float64]
    meridional_wind: npt.NDArray[np.float64]
