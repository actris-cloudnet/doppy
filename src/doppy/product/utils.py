from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class VarResult:
    variance: npt.NDArray[np.float64]
    window_start: npt.NDArray[np.datetime64]
    window_stop: npt.NDArray[np.datetime64]
    nsamples: npt.NDArray[np.int64]
