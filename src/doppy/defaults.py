DEFAULT_BEAM_ENERGY = 1e-5
DEFAULT_EFFECTIVE_DIAMETER = 25e-3


class Halo:
    wavelength = 1.565e-6  # [m]
    receiver_bandwidth = 50e6  # [Hz]
    beam_energy = DEFAULT_BEAM_ENERGY
    effective_diameter = DEFAULT_EFFECTIVE_DIAMETER


class WindCube:
    # https://doi.org/10.5194/essd-13-3539-2021
    wavelength = 1.54e-6  # [m]
    receiver_bandwidth = 55e6  # [Hz]
    beam_energy = DEFAULT_BEAM_ENERGY
    effective_diameter = 50e-3  # [m]
    focus = 1e3  # [m]
