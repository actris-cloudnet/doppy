from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from typing import Sequence, Tuple, TypeAlias

import numpy as np
import numpy.typing as npt
import scipy
from scipy.ndimage import uniform_filter
from sklearn.cluster import KMeans

import doppy
from doppy import defaults, options

SelectionGroupKeyType: TypeAlias = tuple[int,]


@dataclass
class Stare:
    time: npt.NDArray[np.datetime64]
    radial_distance: npt.NDArray[np.float64]
    elevation: npt.NDArray[np.float64]
    beta: npt.NDArray[np.float64]
    radial_velocity: npt.NDArray[np.float64]
    mask: npt.NDArray[np.bool_]
    wavelength: float

    @classmethod
    def from_halo_data(
        cls,
        data: Sequence[str]
        | Sequence[Path]
        | Sequence[bytes]
        | Sequence[BufferedIOBase],
        data_bg: Sequence[str]
        | Sequence[Path]
        | Sequence[tuple[bytes, str]]
        | Sequence[tuple[BufferedIOBase, str]],
        bg_correction_method: options.BgCorrectionMethod,
    ) -> Stare:
        raws = doppy.raw.HaloHpl.from_srcs(data)

        if len(raws) == 0:
            raise doppy.exceptions.NoDataError("HaloHpl data missing")

        raw = (
            doppy.raw.HaloHpl.merge(_select_raws_for_stare(raws))
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
        )

        bgs = doppy.raw.HaloBg.from_srcs(data_bg)
        bgs = [bg[:, : raw.header.ngates] for bg in bgs]
        bgs_stare = [bg for bg in bgs if bg.ngates == raw.header.ngates]

        if len(bgs_stare) == 0:
            raise doppy.exceptions.NoDataError("Background data missing")

        bg = (
            doppy.raw.HaloBg.merge(bgs_stare)
            .sorted_by_time()
            .non_strictly_increasing_timesteps_removed()
        )
        raw, intensity_bg_corrected = _correct_background(raw, bg, bg_correction_method)
        intensity_noise_bias_corrected = _correct_intensity_noise_bias(
            raw, intensity_bg_corrected
        )
        wavelength = defaults.Halo.wavelength
        beta = _compute_beta(
            intensity_noise_bias_corrected,
            raw.radial_distance,
            raw.header.focus_range,
            wavelength,
        )
        mask = _compute_noise_mask(
            intensity_noise_bias_corrected, raw.radial_velocity, raw.radial_distance
        )
        return Stare(
            time=raw.time,
            radial_distance=raw.radial_distance,
            elevation=raw.elevation,
            beta=beta,
            radial_velocity=raw.radial_velocity,
            mask=mask,
            wavelength=wavelength,
        )


def _compute_noise_mask(
    intensity: npt.NDArray[np.float64],
    radial_velocity: npt.NDArray[np.float64],
    radial_distance: npt.NDArray[np.float64],
) -> npt.NDArray[np.bool_]:
    intensity_mean_mask = uniform_filter(intensity, size=(21, 3)) < 1.0025
    velocity_abs_mean_mask = uniform_filter(np.abs(radial_velocity), size=(21, 3)) > 2
    THREE_PULSES_LENGTH = 90
    near_instrument_noise_mask = np.zeros_like(intensity, dtype=np.bool_)
    near_instrument_noise_mask[:, radial_distance < THREE_PULSES_LENGTH] = True
    low_intensity_mask = intensity < 1
    return np.array(
        (intensity_mean_mask & velocity_abs_mean_mask)
        | near_instrument_noise_mask
        | low_intensity_mask,
        dtype=np.bool_,
    )


def _compute_beta(
    intensity: npt.NDArray[np.float64],
    radial_distance: npt.NDArray[np.float64],
    focus: float,
    wavelength: float,
) -> npt.NDArray[np.float64]:
    """
    Parameters
    ----------
    radial_distance
        distance from the instrument
    focus
        focal length of the telescope for the transmitter and receiver
    wavelength
        laser wavelength

    Local variables
    ---------------
    eta
        detector quantum efficiency
    E
        beam energy
    nu
        optical frequency
    h
        planc's constant
    c
        speed of light
    B
        reveiver bandwidth

    References
    ----------
    Methodology for deriving the telescope focus function and
    its uncertainty for a heterodyne pulsed Doppler lidar
        authors:  Pyry Pentikäinen, Ewan James O'Connor,
            Antti Juhani Manninen, and Pablo Ortiz-Amezcua
        doi: https://doi.org/10.5194/amt-13-2849-2020
    """

    snr = intensity - 1
    h = scipy.constants.Planck
    c = scipy.constants.speed_of_light
    eta = 1
    E = 1e-5
    B = 5e7
    nu = c / wavelength
    A_e = _compute_effective_receiver_energy(radial_distance, focus, wavelength)
    beta = 2 * h * nu * B * radial_distance**2 * snr / (eta * c * E * A_e)
    return np.array(beta, dtype=np.float64)


def _compute_effective_receiver_energy(
    radial_distance: npt.NDArray[np.float64],
    focus: float,
    wavelength: float,
) -> npt.NDArray[np.float64]:
    """
    NOTE
    ----
    Using uncalibrated values from https://doi.org/10.5194/amt-13-2849-2020


    Parameters
    ----------
    radial_distance
        distance from the instrument
    focus
        effective focal length of the telescope for the transmitter and receiver
    wavelength
        laser wavelength
    """
    D = 25e-3  # effective_diameter_of_gaussian_beam
    return np.array(
        np.pi
        * D**2
        / (
            4
            * (
                1
                + (np.pi * D**2 / (4 * wavelength * radial_distance)) ** 2
                * (1 - radial_distance / focus) ** 2
            )
        ),
        dtype=np.float64,
    )


def _correct_intensity_noise_bias(
    raw: doppy.raw.HaloHpl, intensity: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """
    Parameters
    ----------
    intensity:
        intensity after background correction
    """
    noise_mask = _locate_noise(intensity)
    # Ignore lower gates
    noise_mask[:, raw.radial_distance <= 90] = False

    A_ = np.concatenate(
        (
            raw.radial_distance[:, np.newaxis],
            np.ones((len(raw.radial_distance), 1)),
        ),
        axis=1,
    )[np.newaxis, :, :]
    A = np.tile(
        A_,
        (len(intensity), 1, 1),
    )
    A_noise = np.tile(noise_mask[:, :, np.newaxis], (1, 1, 2))
    A[~A_noise] = 0
    intensity_ = intensity.copy()
    intensity_[~noise_mask] = 0

    A_pinv = np.linalg.pinv(A)
    x = A_pinv @ intensity_[:, :, np.newaxis]
    noise_fit = (A_ @ x).squeeze(axis=2)
    return np.array(intensity / noise_fit, dtype=np.float64)


def _locate_noise(intensity: npt.NDArray[np.float64]) -> npt.NDArray[np.bool_]:
    """
    Returns
    -------
    boolean array M
        where M[i,j] = True if intensity[i,j] contains only noise
        and False otherwise
    """

    INTENSITY_THRESHOLD = 1.008
    MEDIAN_KERNEL_THRESHOLD = 1.002
    GAUSSIAN_THRESHOLD = 0.02

    intensity_normalised = intensity / np.median(intensity, axis=1)[:, np.newaxis]
    intensity_mask = intensity_normalised > INTENSITY_THRESHOLD

    median_mask = (
        scipy.signal.medfilt2d(intensity_normalised, kernel_size=5)
        > MEDIAN_KERNEL_THRESHOLD
    )

    gaussian = scipy.ndimage.gaussian_filter(
        (intensity_mask | median_mask).astype(np.float64), sigma=8, radius=16
    )
    gaussian_mask = gaussian > GAUSSIAN_THRESHOLD

    return np.array(~(intensity_mask | median_mask | gaussian_mask), dtype=np.bool_)


def _correct_background(
    raw: doppy.raw.HaloHpl,
    bg: doppy.raw.HaloBg,
    method: options.BgCorrectionMethod,
) -> Tuple[doppy.raw.HaloHpl, npt.NDArray[np.float64]]:
    """
    Returns
    -------
    raw_with_bg:
        Same as input raw: HaloHpl, but the profiles that does not corresponding
        background measurement have been removed.


    intensity_bg_corrected:
        intensity = SNR + 1 = (A_0 * P_0(z)) / (A_bg * P_bg(z)), z = radial_distance
        The measured background signal P_bg contains usually lots of noise that shows as
        vertical stripes in intensity plots. In bg corrected intensity, P_bg is replaced
        with corrected background profile that should represent the noise floor
        more accurately
    """
    bg_relevant = _select_relevant_background_profiles(bg, raw.time)
    match method:
        case options.BgCorrectionMethod.FIT:
            bg_signal_corrected = _correct_background_by_fitting(
                bg_relevant, raw.radial_distance, fit_method=None
            )
        case options.BgCorrectionMethod.MEAN:
            raise NotImplementedError
        case options.BgCorrectionMethod.PRE_COMPUTED:
            raise NotImplementedError

    raw2bg = np.searchsorted(bg_relevant.time, raw.time, side="right") - 1
    raw_with_bg = raw[raw2bg >= 0]
    raw2bg = raw2bg[raw2bg >= 0]
    raw_bg_original = bg_relevant.signal[raw2bg]
    raw_bg_corrected = bg_signal_corrected[raw2bg]

    intensity_bg_corrected = raw_with_bg.intensity * raw_bg_original / raw_bg_corrected
    return raw_with_bg, intensity_bg_corrected


def _correct_background_by_fitting(
    bg: doppy.raw.HaloBg,
    radial_distance: npt.NDArray[np.float64],
    fit_method: options.BgFitMethod | None,
) -> npt.NDArray[np.float64]:
    clusters = _cluster_background_profiles(bg.signal, radial_distance)
    signal_correcred = np.zeros_like(bg.signal)
    for cluster in set(clusters):
        signal_correcred[clusters == cluster] = _fit_background(
            bg[clusters == cluster], radial_distance, fit_method
        )
    return signal_correcred


def _fit_background(
    bg: doppy.raw.HaloBg,
    radial_distance: npt.NDArray[np.float64],
    fit_method: options.BgFitMethod | None,
) -> npt.NDArray[np.float64]:
    if fit_method is None:
        fit_method = _infer_fit_type(bg.signal, radial_distance)
    match fit_method:
        case options.BgFitMethod.LIN:
            return _linear_fit(bg.signal, radial_distance)
        case options.BgFitMethod.EXP:
            return _exponential_fit(bg.signal, radial_distance)
        case options.BgFitMethod.EXPLIN:
            return _exponential_linear_fit(bg.signal, radial_distance)


def _lin_func(
    x: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    return np.array(x[0] * radial_distance + x[1], dtype=np.float64)


def _exp_func(
    x: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    return np.array(x[0] * np.exp(x[1] * radial_distance ** x[2]), dtype=np.float64)


def _explin_func(
    x: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    return np.array(
        _exp_func(x[:3], radial_distance) + _lin_func(x[3:], radial_distance),
        dtype=np.float64,
    )


def _infer_fit_type(
    bg_signal: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> options.BgFitMethod:
    peaks = _detect_peaks(bg_signal, radial_distance)
    dist_mask = (90 < radial_distance) & (radial_distance < 8000)
    mask = dist_mask & ~peaks

    scale = np.median(bg_signal, axis=1)[:, np.newaxis]

    rdist = radial_distance[np.newaxis][:, mask]

    signal = (bg_signal / scale)[:, mask]

    def lin_func_rss(x: npt.NDArray[np.float64]) -> np.float64:
        return np.float64(((signal - _lin_func(x, rdist)) ** 2).sum())

    def exp_func_rss(x: npt.NDArray[np.float64]) -> np.float64:
        return np.float64(((signal - _exp_func(x, rdist)) ** 2).sum())

    def explin_func_rss(x: npt.NDArray[np.float64]) -> np.float64:
        return np.float64(((signal - _explin_func(x, rdist)) ** 2).sum())

    method = "Nelder-Mead"
    res_lin = scipy.optimize.minimize(
        lin_func_rss, [1e-5, 1], method=method, options={"maxiter": 2 * 600}
    )
    res_exp = scipy.optimize.minimize(
        exp_func_rss, [1, -1, -1], method=method, options={"maxiter": 3 * 600}
    )
    res_explin = scipy.optimize.minimize(
        explin_func_rss, [1, -1, -1, 0, 0], method=method, options={"maxiter": 5 * 600}
    )

    fit_lin = _lin_func(res_lin.x, rdist)
    fit_exp = _exp_func(res_exp.x, rdist)
    fit_explin = _explin_func(res_explin.x, rdist)

    lin_rss = ((signal - fit_lin) ** 2).sum()
    exp_rss = ((signal - fit_exp) ** 2).sum()
    explin_rss = ((signal - fit_explin) ** 2).sum()

    #
    if exp_rss / lin_rss < 0.95 or explin_rss / lin_rss < 0.95:
        if (exp_rss - explin_rss) / lin_rss > 0.05:
            return options.BgFitMethod.EXPLIN
        else:
            return options.BgFitMethod.EXP
    else:
        return options.BgFitMethod.LIN


def _detect_peaks(
    background_signal: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.bool_]:
    """
    background_signal: dim = (time,range)
    radial_distance: dim = (range,)

    Returns a boolean mask, dim = (range, ), where True denotes locations of peaks
    that should be ignored in fitting
    """
    scale = np.median(background_signal, axis=1)[:, np.newaxis]
    bg = background_signal / scale
    return _set_adjacent_true(
        np.concatenate(
            (
                np.array([False]),
                np.diff(np.diff(bg.mean(axis=0))) < -0.01,
                np.array([False]),
            )
        )
    )


def _set_adjacent_true(arr: npt.NDArray[np.bool_]) -> npt.NDArray[np.bool_]:
    temp = np.pad(arr, (1, 1), mode="constant")
    temp[:-2] |= arr
    temp[2:] |= arr
    return temp[1:-1]


def _linear_fit(
    bg_signal: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    dist_mask = 90 < radial_distance
    peaks = _detect_peaks(bg_signal, radial_distance)
    mask = dist_mask & ~peaks

    scale = np.median(bg_signal, axis=1)[:, np.newaxis]
    rdist_fit = radial_distance[np.newaxis][:, mask]
    signal_fit = (bg_signal / scale)[:, mask]

    A = np.tile(
        np.concatenate((rdist_fit, np.ones_like(rdist_fit))).T, (signal_fit.shape[0], 1)
    )
    x = np.linalg.pinv(A) @ signal_fit.reshape(-1, 1)
    fit = (
        np.concatenate(
            (radial_distance[:, np.newaxis], np.ones((radial_distance.shape[0], 1))),
            axis=1,
        )
        @ x
    ).T
    return np.array(fit * scale, dtype=np.float64)


def _exponential_fit(
    bg_signal: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    dist_mask = 90 < radial_distance
    peaks = _detect_peaks(bg_signal, radial_distance)
    mask = dist_mask & ~peaks
    scale = np.median(bg_signal, axis=1)[:, np.newaxis]
    rdist_fit = radial_distance[np.newaxis][:, mask]
    signal_fit = (bg_signal / scale)[:, mask]

    def exp_func_rss(x: npt.NDArray[np.float64]) -> np.float64:
        return np.float64(((signal_fit - _exp_func(x, rdist_fit)) ** 2).sum())

    result = scipy.optimize.minimize(
        exp_func_rss, [1, -1, -1], method="Nelder-Mead", options={"maxiter": 3 * 600}
    )
    fit = _exp_func(result.x, radial_distance)[np.newaxis, :]
    return np.array(fit * scale, dtype=np.float64)


def _exponential_linear_fit(
    bg_signal: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    dist_mask = 90 < radial_distance
    peaks = _detect_peaks(bg_signal, radial_distance)
    mask = dist_mask & ~peaks
    scale = np.median(bg_signal, axis=1)[:, np.newaxis]
    rdist_fit = radial_distance[np.newaxis][:, mask]
    signal_fit = (bg_signal / scale)[:, mask]

    def explin_func_rss(x: npt.NDArray[np.float64]) -> np.float64:
        return np.float64(((signal_fit - _explin_func(x, rdist_fit)) ** 2).sum())

    result = scipy.optimize.minimize(
        explin_func_rss,
        [1, -1, -1, 0, 0],
        method="Nelder-Mead",
        options={"maxiter": 5 * 600},
    )
    fit = _explin_func(result.x, radial_distance)[np.newaxis, :]
    return np.array(fit * scale, dtype=np.float64)


def _select_raws_for_stare(
    raws: Sequence[doppy.raw.HaloHpl],
) -> Sequence[doppy.raw.HaloHpl]:
    groups: dict[SelectionGroupKeyType, int] = defaultdict(int)

    if len(raws) == 0:
        raise doppy.exceptions.NoDataError("No data to select from")

    # Select files that stare
    raws_stare = [raw for raw in raws if len(raw.azimuth_angles) == 1]
    if len(raws_stare) == 0:
        raise doppy.exceptions.NoDataError(
            "No data suitable for stare product. Data is probably from scans"
        )
    raws_stare = [raw for raw in raws if len(raw.elevation_angles) == 1]
    if len(raws_stare) == 0:
        raise doppy.exceptions.NoDataError(
            "No data suitable for stare product. "
            "Elevation angle does not remain constant"
        )
    elevation_angles = []
    for raw in raws_stare:
        elevation_angles += list(raw.elevation_angles)
    max_elevation_angle = max(elevation_angles)

    ELEVATION_ANGLE_FLUCTUATION_THRESHOLD = 2
    ELEVATION_ANGLE_VERTICAL_OFFSET_THRESHOLD = 15

    raws_stare = [
        raw
        for raw in raws
        if abs(next(iter(raw.elevation_angles)) - max_elevation_angle)
        < ELEVATION_ANGLE_FLUCTUATION_THRESHOLD
        and abs(next(iter(raw.elevation_angles)) - 90)
        < ELEVATION_ANGLE_VERTICAL_OFFSET_THRESHOLD
    ]

    if len(raws_stare) == 0:
        raise doppy.exceptions.NoDataError("No data suitable for stare product")

    # count the number of profiles each (scan_type,ngates) group has
    for raw in raws_stare:
        groups[_selection_key(raw)] += len(raw.time)

    def key_func(key: SelectionGroupKeyType) -> int:
        return groups[key]

    # (scan_type,ngates, gate_points) group with the most profiles
    select_tuple = max(groups, key=key_func)

    return [raw for raw in raws_stare if _selection_key(raw) == select_tuple]


def _selection_key(raw: doppy.raw.HaloHpl) -> SelectionGroupKeyType:
    return (raw.header.mergable_hash(),)


def _time2bg_time(
    time: npt.NDArray[np.datetime64], bg_time: npt.NDArray[np.datetime64]
) -> npt.NDArray[np.int64]:
    return np.searchsorted(bg_time, time, side="right") - 1


def _select_relevant_background_profiles(
    bg: doppy.raw.HaloBg, time: npt.NDArray[np.datetime64]
) -> doppy.raw.HaloBg:
    """
    expects bg.time to be sorted
    """
    time2bg_time = _time2bg_time(time, bg.time)

    relevant_indices = list(set(time2bg_time[time2bg_time >= 0]))
    bg_ind = np.arange(bg.time.size)
    is_relevant = np.isin(bg_ind, relevant_indices)
    return bg[is_relevant]


def _cluster_background_profiles(
    background_signal: npt.NDArray[np.float64], radial_distance: npt.NDArray[np.float64]
) -> npt.NDArray[np.int64]:
    default_labels = np.zeros(len(background_signal), dtype=int)
    if len(background_signal) < 2:
        return default_labels
    radial_distance_mask = (90 < radial_distance) & (radial_distance < 1500)

    normalised_background_signal = background_signal / np.median(
        background_signal, axis=1, keepdims=True
    )

    profile_median = np.median(
        normalised_background_signal[:, radial_distance_mask], axis=1
    )
    kmeans = KMeans(n_clusters=2, n_init="auto").fit(profile_median[:, np.newaxis])
    cluster_width = np.array([None, None])
    for label in [0, 1]:
        cluster = profile_median[kmeans.labels_ == label]
        cluster_width[label] = np.max(cluster) - np.min(cluster)
    cluster_distance = np.abs(
        kmeans.cluster_centers_[0, 0] - kmeans.cluster_centers_[1, 0]
    )
    max_cluster_width = np.float64(np.max(cluster_width))
    if np.isclose(max_cluster_width, 0):
        return default_labels
    if cluster_distance / max_cluster_width > 3:
        return np.array(kmeans.labels_, dtype=np.int64)
    return default_labels
