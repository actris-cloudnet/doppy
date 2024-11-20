DEFAULT_BEAM_ENERGY = 1e-5


class Halo:
    wavelength = 1.565e-6  # [m]
    receiver_bandwidth = 50e6  # [Hz]
    beam_energy = DEFAULT_BEAM_ENERGY


class WindCube:
    # https://doi.org/10.5194/essd-13-3539-2021
    wavelength = 1.54e-6  # [m]
    receiver_bandwidth = 55e6  # [Hz]
    beam_energy = DEFAULT_BEAM_ENERGY
