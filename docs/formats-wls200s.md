# Format 1

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(sweep)
  comments: Number of sweeps in the dataset.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  scan_file_name: <SCAN_FILE_NAME>
  scan_id: <SCAN_ID>
  settings_file_name: <SETTINGS_FILE_NAME>
  settings_id: <SETTINGS_ID>
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(horizontal_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Norm of the wind projection on local horizontal plane.
    standard_name: wind_speed
    units: m s-1
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(scan_file)
    comments: Binary content of scan file.
  Variable(settings_file)
    comments: Binary content of settings file.
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(time_reference)
    comments: UTC reference date. Format follows ISO 8601 standard.
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
  Variable(vertical_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Vertical component of the wind. Positive towards zenith.
    standard_name: upward_air_velocity
    units: m s-1
  Variable(wind_direction)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Wind direction with respect to true north, (0=wind coming from the north, 90=east, 180=south, 270=west)
    standard_name: wind_from_direction
    units: degrees
  Variable(wind_speed_ci)
    comments: For inclined lines of sight this figure is equal to 0, 75 or 100 depending on the number of line of sight used for the reconstruction (maximum 4 lines of sight are used). For vertical lines of sight this figure is equal to 100 when the status of the radial wind speed is equal to 1.
    is_quality_field: true
    long_name: wind_speed_confidence_index
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
    units: percent
  Variable(wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if its confidence index is lower than 100.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: wind_speed_status
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- dbs, [cabauw](https://cloudnet.fmi.fi/site/cabauw)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2022-02-21_13-21-59_dbs_495_100m.nc](https://cloudnet.fmi.fi/api/download/raw/b0359380-d1c0-4ccf-a22e-c4aac779fbe2/WLS200s-218_2022-02-21_13-21-59_dbs_495_100m.nc)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2022-05-26_18-17-38_dbs_865_50m.nc](https://cloudnet.fmi.fi/api/download/raw/0e47de48-827f-4830-b574-6d9694d99093/WLS200s-218_2022-05-26_18-17-38_dbs_865_50m.nc)

# Format 2

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(sweep)
  comments: Number of sweeps in the dataset.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  scan_file_name: <SCAN_FILE_NAME>
  scan_id: <SCAN_ID>
  settings_file_name: <SETTINGS_FILE_NAME>
  settings_id: <SETTINGS_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(scan_file)
    comments: Binary content of scan file.
  Variable(settings_file)
    comments: Binary content of settings file.
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(time_reference)
    comments: UTC reference date. Format follows ISO 8601 standard.
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- fixed, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200S-197_2021-11-05_08-01-15_fixed_273_100m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/fc97cd38-620e-4912-8749-d85fc6e3e11b/WLS200S-197_2021-11-05_08-01-15_fixed_273_100m.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200S-197_2021-11-23_09-31-25_fixed_145_100m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/72e9977a-2f2b-41bb-a639-c2a3ffbe2d32/WLS200S-197_2021-11-23_09-31-25_fixed_145_100m.nc.gz)

# Format 3

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(horizontal_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Norm of the wind projection on local horizontal plane.
    standard_name: wind_speed
    units: m s-1
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
  Variable(vertical_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Vertical component of the wind. Positive towards zenith.
    standard_name: upward_air_velocity
    units: m s-1
  Variable(wind_direction)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Wind direction with respect to true north, (0=wind coming from the north, 90=east, 180=south, 270=west)
    standard_name: wind_from_direction
    units: degrees
  Variable(wind_speed_ci)
    comments: For inclined lines of sight this figure is equal to 0, 75 or 100 depending on the number of line of sight used for the reconstruction (maximum 4 lines of sight are used). For vertical lines of sight this figure is equal to 100 when the status of the radial wind speed is equal to 1.
    is_quality_field: true
    long_name: wind_speed_confidence_index
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
    units: percent
  Variable(wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if its confidence index is lower than 100.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: wind_speed_status
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- dbs, [cabauw](https://cloudnet.fmi.fi/site/cabauw)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2024-12-28_05-37-06_dbs_65_100m.nc](https://cloudnet.fmi.fi/api/download/raw/9238daf6-2979-4729-b07c-9eb288482d38/WLS200s-218_2024-12-28_05-37-06_dbs_65_100m.nc)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2024-11-23_00-44-21_dbs_65_100m.nc](https://cloudnet.fmi.fi/api/download/raw/e816c953-d1a6-45b3-8102-2faca262bd3a/WLS200s-218_2024-11-23_00-44-21_dbs_65_100m.nc)

# Format 4

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(horizontal_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Norm of the wind projection on local horizontal plane.
    standard_name: wind_speed
    units: m s-1
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
  Variable(vertical_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Vertical component of the wind. Positive towards zenith.
    standard_name: upward_air_velocity
    units: m s-1
  Variable(wind_direction)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Wind direction with respect to true north, (0=wind coming from the north, 90=east, 180=south, 270=west)
    standard_name: wind_from_direction
    units: degrees
  Variable(wind_speed_ci)
    comments: For inclined lines of sight this figure is equal to 0, 75 or 100 depending on the number of line of sight used for the reconstruction (maximum 4 lines of sight are used). For vertical lines of sight this figure is equal to 100 when the status of the radial wind speed is equal to 1.
    is_quality_field: true
    long_name: wind_speed_confidence_index
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
    units: percent
  Variable(wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if its confidence index is lower than 100.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: wind_speed_status
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- dbs, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2023-09-22_05-36-12_dbs_303_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/b68b2e4d-3b30-4046-8f8f-2b6c8e95572b/WLS200s-197_2023-09-22_05-36-12_dbs_303_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2023-04-08_23-08-46_dbs_303_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/7c36438e-c878-4e93-96de-e2ee87790d91/WLS200s-197_2023-04-08_23-08-46_dbs_303_50mTP.nc.gz)

# Format 5

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(horizontal_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Norm of the wind projection on local horizontal plane.
    standard_name: wind_speed
    units: m s-1
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
  Variable(vertical_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Vertical component of the wind. Positive towards zenith.
    standard_name: upward_air_velocity
    units: m s-1
  Variable(wind_direction)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Wind direction with respect to true north, (0=wind coming from the north, 90=east, 180=south, 270=west)
    standard_name: wind_from_direction
    units: degrees
  Variable(wind_speed_ci)
    comments: For inclined lines of sight this figure is equal to 0, 75 or 100 depending on the number of line of sight used for the reconstruction (maximum 4 lines of sight are used). For vertical lines of sight this figure is equal to 100 when the status of the radial wind speed is equal to 1.
    is_quality_field: true
    long_name: wind_speed_confidence_index
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
    units: percent
  Variable(wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if its confidence index is lower than 100.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: wind_speed_status
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- dbs, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-02-09_12-17-12_dbs_156_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/b20bd9f5-fd4a-4b69-ab3e-4d9e5d4b6073/WLS200s-197_2022-02-09_12-17-12_dbs_156_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-05-10_22-58-12_dbs_320_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/8adf75f8-0dc3-44f3-b4b6-155fcde86d4e/WLS200s-197_2022-05-10_22-58-12_dbs_320_50mTP.nc.gz)

# Format 6

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume,multifixed
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- ppi, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2025-02-13_18-41-39_ppi_358_XXm.nc.gz](https://cloudnet.fmi.fi/api/download/raw/20e66415-5fd3-4892-89ad-ec0e3d64a8cc/WLS200s-197_2025-02-13_18-41-39_ppi_358_XXm.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2025-02-15_14-11-52_ppi_360_100m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/594ba74f-a5fa-47f8-8a61-60daf7baca4a/WLS200s-197_2025-02-15_14-11-52_ppi_360_100m.nc.gz)

# Format 7

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(sweep)
  comments: Number of sweeps in the dataset.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  scan_file_name: <SCAN_FILE_NAME>
  scan_id: <SCAN_ID>
  settings_file_name: <SETTINGS_FILE_NAME>
  settings_id: <SETTINGS_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(horizontal_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Norm of the wind projection on local horizontal plane.
    standard_name: wind_speed
    units: m s-1
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(scan_file)
    comments: Binary content of scan file.
  Variable(settings_file)
    comments: Binary content of settings file.
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(time_reference)
    comments: UTC reference date. Format follows ISO 8601 standard.
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
  Variable(vertical_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Vertical component of the wind. Positive towards zenith.
    standard_name: upward_air_velocity
    units: m s-1
  Variable(wind_direction)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Wind direction with respect to true north, (0=wind coming from the north, 90=east, 180=south, 270=west)
    standard_name: wind_from_direction
    units: degrees
  Variable(wind_speed_ci)
    comments: For inclined lines of sight this figure is equal to 0, 75 or 100 depending on the number of line of sight used for the reconstruction (maximum 4 lines of sight are used). For vertical lines of sight this figure is equal to 100 when the status of the radial wind speed is equal to 1.
    is_quality_field: true
    long_name: wind_speed_confidence_index
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
    units: percent
  Variable(wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if its confidence index is lower than 100.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: wind_speed_status
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- dbs, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200S-197_2021-10-25_20-30-13_dbs_264_50m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/e43bc58c-7cfb-48c3-83d1-4d39e17f58d1/WLS200S-197_2021-10-25_20-30-13_dbs_264_50m.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200S-197_2021-07-28_15-57-00_dbs_270_100m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/ddac522f-5757-4a35-8658-06eb3a4c58e9/WLS200S-197_2021-07-28_15-57-00_dbs_270_100m.nc.gz)

# Format 8

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- rhi, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-01-24_10-44-05_rhi_168_200m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/0f331f3e-630e-4f6f-ab38-fc7cc0aa8e30/WLS200s-197_2022-01-24_10-44-05_rhi_168_200m.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-02-09_18-44-03_rhi_168_200m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/7b6c1e98-4312-4f0a-958f-dbb3e987b2fb/WLS200s-197_2022-02-09_18-44-03_rhi_168_200m.nc.gz)
- fixed, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-02-26_17-32-33_fixed_134_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/55d3d8aa-bfc9-45f6-bc97-4b2c1a01370b/WLS200s-197_2022-02-26_17-32-33_fixed_134_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-04-19_16-25-29_fixed_119_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/7dc24953-e461-402c-9c7a-d8a0c3fcc094/WLS200s-197_2022-04-19_16-25-29_fixed_119_50mTP.nc.gz)
- ppi, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-04-26_15-37-18_ppi_300_25mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/9a5463f8-ac6f-4a0c-b7db-967760fd5155/WLS200s-197_2022-04-26_15-37-18_ppi_300_25mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-06-01_14-34-22_ppi_312_100m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/4b2762b7-9aca-4e5c-9b9c-e0a4ca9fce77/WLS200s-197_2022-06-01_14-34-22_ppi_312_100m.nc.gz)
- volume, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-03-17_20-12-47_volume_127_50m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/6e4de24f-1c05-42ec-baa6-9b759d270cc9/WLS200s-197_2022-03-17_20-12-47_volume_127_50m.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-03-11_18-14-11_volume_129_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/c22b528f-001e-4d7e-b47d-2b3f0838f99b/WLS200s-197_2022-03-11_18-14-11_volume_129_50mTP.nc.gz)

# Format 9

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- fixed, [cabauw](https://cloudnet.fmi.fi/site/cabauw)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2024-08-17_14-30-09_fixed_48_75m.nc](https://cloudnet.fmi.fi/api/download/raw/21852fc1-a1e5-4e3c-b847-744c4b917f9f/WLS200s-218_2024-08-17_14-30-09_fixed_48_75m.nc)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2024-08-08_22-30-18_fixed_48_75m.nc](https://cloudnet.fmi.fi/api/download/raw/97acbd66-8ae5-43e9-a4aa-ce20dae782fc/WLS200s-218_2024-08-08_22-30-18_fixed_48_75m.nc)

# Format 10

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(horizontal_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Norm of the wind projection on local horizontal plane.
    standard_name: wind_speed
    units: m s-1
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume,multifixed
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
  Variable(vertical_wind_speed)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Vertical component of the wind. Positive towards zenith.
    standard_name: upward_air_velocity
    units: m s-1
  Variable(wind_direction)
    ancilliary_variables: wind_speed_ci,wind_speed_status
    comments: Wind direction with respect to true north, (0=wind coming from the north, 90=east, 180=south, 270=west)
    standard_name: wind_from_direction
    units: degrees
  Variable(wind_speed_ci)
    comments: For inclined lines of sight this figure is equal to 0, 75 or 100 depending on the number of line of sight used for the reconstruction (maximum 4 lines of sight are used). For vertical lines of sight this figure is equal to 100 when the status of the radial wind speed is equal to 1.
    is_quality_field: true
    long_name: wind_speed_confidence_index
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
    units: percent
  Variable(wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if its confidence index is lower than 100.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: wind_speed_status
    qualified_variables: horizontal_wind_speed,vertical_wind_speed,wind_direction
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- dbs, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2025-02-15_13-15-34_dbs_470_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/19ed2628-7bf7-474f-a97d-7f30bd404d4f/WLS200s-197_2025-02-15_13-15-34_dbs_470_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2025-02-17_11-08-45_dbs_470_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/b9f5b5f0-fbe1-48f3-9ae5-d5c0d1400857/WLS200s-197_2025-02-17_11-08-45_dbs_470_50mTP.nc.gz)

# Format 11

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(sweep)
  comments: Number of sweeps in the dataset.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  scan_file_name: <SCAN_FILE_NAME>
  scan_id: <SCAN_ID>
  settings_file_name: <SETTINGS_FILE_NAME>
  settings_id: <SETTINGS_ID>
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(scan_file)
    comments: Binary content of scan file.
  Variable(settings_file)
    comments: Binary content of settings file.
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(time_reference)
    comments: UTC reference date. Format follows ISO 8601 standard.
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- fixed, [cabauw](https://cloudnet.fmi.fi/site/cabauw)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2023-09-30_07-40-05_fixed_1864_50m_200s.nc](https://cloudnet.fmi.fi/api/download/raw/0cdab1ff-1e49-49fa-8c81-25a1b20c129d/WLS200s-218_2023-09-30_07-40-05_fixed_1864_50m_200s.nc)
  - [cabauw](https://hdl.handle.net/21.12132/3.dca88604798e4647), [WLS200s-218_2022-03-24_09-01-05_fixed_492_100m.nc](https://cloudnet.fmi.fi/api/download/raw/1374570e-8156-4a1f-a794-b54a7979b991/WLS200s-218_2022-03-24_09-01-05_fixed_492_100m.nc)

# Format 12

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- vad, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2023-03-06_20-51-37_vad_148_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/cdcb69bd-4429-4b4f-b09d-073452b13a70/WLS200s-197_2023-03-06_20-51-37_vad_148_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2024-03-16_08-21-33_vad_148_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/67e17aa8-a381-4dcd-a712-8ad0789a7a4b/WLS200s-197_2024-03-16_08-21-33_vad_148_50mTP.nc.gz)

# Format 13

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- ppi, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2024-02-20_18-42-05_ppi_66_50m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/e39dabcd-6bea-4696-afc9-e1e86c472dd0/WLS200s-197_2024-02-20_18-42-05_ppi_66_50m.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-07-05_05-46-09_ppi_207_150m.nc.gz](https://cloudnet.fmi.fi/api/download/raw/6bccf32e-5608-4ade-8016-efc7023945a4/WLS200s-197_2022-07-05_05-46-09_ppi_207_150m.nc.gz)
- fixed, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2024-02-01_20-31-33_fixed_287_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/ab8df62c-369b-4773-9597-a5320e24c29b/WLS200s-197_2024-02-01_20-31-33_fixed_287_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2025-01-17_17-01-33_fixed_287_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/895dd963-fe14-482d-82f6-3e68585b0403/WLS200s-197_2025-01-17_17-01-33_fixed_287_50mTP.nc.gz)

# Format 14

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since time_reference
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- vad, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-03-21_05-40-29_vad_157_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/7830af20-353f-480f-8fd0-4dbe1437051e/WLS200s-197_2022-03-21_05-40-29_vad_157_50mTP.nc.gz)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2022-03-21_21-08-45_vad_157_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/0241e5b3-ec31-4dd5-be0b-189326fc79fb/WLS200s-197_2022-03-21_21-08-45_vad_157_50mTP.nc.gz)

# Format 15

```
comment: <COMMENT>
Conventions: <CONVENTIONS>
history: <HISTORY>
institution: <INSTITUTION>
instrument_name: <INSTRUMENT_NAME>
references:
scan_file_name: <SCAN_FILE_NAME>
scan_id: <SCAN_ID>
settings_file_name: <SETTINGS_FILE_NAME>
settings_id: <SETTINGS_ID>
source: <SOURCE>
title: <TITLE>
Variable(altitude)
  comments: Altitude of instrument above mean sea level in WGS-84. For a mobile platform, this is the altitude at the start of the volume.
  standard_name: altitude
  units: m
Variable(default_altitude)
  comments: Default altitude of instrument above mean see level
  long_name: default_altitude
  units: m
Variable(default_latitude)
  comments: Default latitude of instrument
  long_name: default_latitude
  units: degrees_north
Variable(default_longitude)
  comments: Default longitude of instrument
  long_name: default_longitude
  units: degrees_east
Variable(instrument_type)
  option: radar,lidar
Variable(latitude)
  comments: Latitude of instrument in WGS-84. For a mobile platform, this is the latitude at the start of the volume.
  standard_name: latitude
  units: degrees_north
Variable(lidar_model)
  comments: Model of lidar
  long_name: lidar_model
Variable(longitude)
  comments: Longitude of instrument in WGS-84. For a mobile platform, this is the longitude at the start of the volume.
  standard_name: longitude
  units: degrees_east
Variable(scan_file)
  comments: Binary content of scan file.
Variable(sequence_index)
  comments: Identification number of the current sequence
  long_name: sequence_index
Variable(settings_file)
  comments: Binary content of settings file.
Variable(sweep_fixed_angle)
  comments: Array of angles of each sweep in file. Azimuth(s) for RHI, elevation(s) for other modes including FIXED line of sight.
  units: degrees
Variable(sweep_group_name)
  comments: Array of names of each sweep group in file.
Variable(time_reference)
  comments: UTC reference date. Format follows ISO 8601 standard.
  long_name: time_reference
Variable(time_zone)
  comments: Local time offset from Coordinated Universal Time (UTC).
  long_name: time_zone
  units: s
Group: Sweep_INDEX
  res_file_name: <RES_FILE_NAME>
  res_id: <RES_ID>
  Variable(absolute_beta)
    comments: Attenuated absolute backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(atmospherical_structures_type)
    comments: Atmospherical structures detected out of the planetary boundary layer.
    flag_masks: 0,20,30,200,300,400,2000,3000,4000
    flag_meanings: No data or no detection, residual layer, mixed layer , unclassified cloud, ice cloud, water cloud, unclassified aerosol , spherical aerosol, aspherical aerosol
    long_name: atmospherical_structures_type
  Variable(azimuth)
    axis: radial_azimuth_coordinate
    comments: Scanning head's azimuth angle relative to true north when each measurement finished. 0 to 360. 0 is the North, 90 is the East. This angle only incorporates azimuth_correction. The Lidar is not supposed to be moving.
    long_name: azimuth_angle_from_true_north
    standard_name: ray_azimuth_angle
    units: degrees
  Variable(cnr)
    standard_name: carrier_to_noise_ratio
    units: dB
  Variable(doppler_spectrum_mean_error)
    comments: Root Mean Square Error between the measured Doppler spectrum and the estimated Doppler spectrum.
    long_name: doppler_spectrum_mean_error
    units: percent
  Variable(doppler_spectrum_width)
    comments: Full width at half maximum of the spectrum. Representative of particules speed dispersion in the range gate.
    standard_name: doppler_spectrum_width
    units: m s-1
  Variable(elevation)
    axis: radial_elevation_coordinate
    comments: Scanning head's elevation angle relative to horizontal plane when each measurement finished. -90 to 90. 90 is the zenith. This angle does not incorporate any automatic corrections. The Lidar is not supposed to be moving.
    long_name: elevation_angle_from_horizontal_plane
    standard_name: ray_elevation_angle
    units: degrees
  Variable(gate_index)
    comments: Identification number of each range gate. Either a dimension or a variable. When this vector is a dimension, range is a variable and vice versa.
    long_name: gate_index
  Variable(instrumental_function_amplitude)
    ancilliary_variables: instrumental_function_status
    comments: Amplitude of variations of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_amplitude
    units: dB
  Variable(instrumental_function_half_height_width)
    ancilliary_variables: instrumental_function_status
    comments: Scale parameter specifying the half height width of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_half_height_width
    units: m
  Variable(instrumental_function_status)
    comments: 0 for rejected data and 1 for accepted data. Data is rejected if the beta calibration is not successful.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: instrumental_function_status
    qualified_variables: instrumental_function_x_max,instrumental_function_y_average,instrumental_function_amplitude,instrumental_function_half_height_width
  Variable(instrumental_function_x_max)
    ancilliary_variables: instrumental_function_status
    comments: Maximum horizontal axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_x_max
    units: m
  Variable(instrumental_function_y_average)
    ancilliary_variables: instrumental_function_status
    comments: Average value of the y-axis of the Lorentz distribution obtained in the last calibration.
    long_name: instrumental_function_y_average
    units: dB
  Variable(measurement_height)
    comments: Vertical distance normal to the ground, between the instrument and the center of each range gate.
    meters_between_gates: <METERS_BETWEEN_GATES>
    meters_to_center_of_first_gate: <METERS_TO_CENTER_OF_FIRST_GATE>
    standard_name: height
    units: m
  Variable(radial_wind_speed)
    ancilliary_variables: radial_wind_speed_ci,radial_wind_speed_status
    comments: Wind speed vector projected along the line of sights.
    standard_name: radial_velocity_of_scatterers_away_from_instrument
    units: m s-1
  Variable(radial_wind_speed_ci)
    comments: Quality indicator between 0 and 100.
    is_quality_field: true
    long_name: radial_wind_speed_confidence_index
    qualified_variables: radial_wind_speed
    units: percent
  Variable(radial_wind_speed_status)
    comments: 0 for rejected data and 1 for accepted data. A data is rejected if the confidence index is below a threshold calibrated in factory or when radial wind speed is out of the accepted range.
    flag_meanings: rejected,accepted
    flag_values: 0b,1b
    is_quality_field: true
    long_name: radial_wind_speed_status
    qualified_variables: radial_wind_speed
  Variable(range)
    axis: radial_range_coordinate
    comments: Distance along the line of sight, between the instrument and the center of each range gate. Either a dimension or a variable. When this vector is a dimension, gate_index is a variable and vice versa.
    long_name: range_to_measurement_volume
    spacing_is_constant: <SPACING_IS_CONSTANT>
    standard_name: projection_range_coordinate
    units: m
  Variable(range_gate_length)
    comments: Radial dimension of range gates
    long_name: range_gate_length
    units: m
  Variable(ray_accumulation_time)
    comments: Time during which the detector collects light. A ray is defined by this duration.
    long_name: ray_accumulation_time
    units: ms
  Variable(ray_angle_resolution)
    comments: Angle between the center of  two consecutive rays when scanning head's angular speed, and accumulation time are constants.
    long_name: angular_resolution
    units: degrees
  Variable(ray_index)
    comments: Identification number of each ray.
    long_name: ray_index
  Variable(relative_beta)
    comments: Attenuated relative backscatter coefficient. Processed from the CNR.
    standard_name: volume_attenuated_backwards_scattering_function_in_air
    units: m-1 sr-1
  Variable(res_file)
    comments: Binary content of res file.
  Variable(rotation_direction)
    long_name: rotation_direction_of_scanning_head
    option: direct,indirect
  Variable(sweep_index)
    comments: Identification number of the current sweep.
    long_name: sweep_index
  Variable(sweep_mode)
    long_name: scanning_mode_of_current_sweep
    option: sector,coplane,rhi,ppi,vertical_pointing,idle,azimuth_surveillance,elevation_surveillance,sunscan,fixed,manual_ppi,manual_rhi,dbs,segment,vad,volume,multifixed
  Variable(time)
    calendar: gregorian
    comments: Number of seconds between time_reference and the end of each ray measurement.
    standard_name: time
    units: seconds since 1970-01-01T00:00:00Z
  Variable(timestamp)
    comments: Timestamp at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp
  Variable(timestamp_local)
    comments: Timestamp in local timezone at the end of each ray measurement following  ISO8601 standard
    long_name: timestamp_local
Group: georeference_correction
  Variable(azimuth_correction)
    comments: Azimuth offset angle used if the Lidar cannot be physically oriented to the North.
    long_name: instrument_azimuth_offset
    units: degrees
Group: lidar_calibration_group
  Variable(default_instrumental_function_amplitude)
    comments: Default amplitude of variations of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_amplitude
    units: dB
  Variable(default_instrumental_function_half_height_width)
    comments: Default scale parameter specifying the half height width of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_half_height_width
    units: m
  Variable(default_instrumental_function_x_max)
    comments: Default maximum horizontal axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_x_max
    units: m
  Variable(default_instrumental_function_y_average)
    comments: Default average value of the y-axis of the Lorentz distribution used for beta computation.
    long_name: default_instrumental_function_y_average
    units: dB
```

## Example files

- vad, [payerne](https://cloudnet.fmi.fi/site/payerne)
  - [payerne](https://hdl.handle.net/21.12132/3.a3c0f804d91e4966), [WLS200s-197_2025-02-17_16-51-32_vad_469_50mTP.nc.gz](https://cloudnet.fmi.fi/api/download/raw/150e5416-0fb8-4386-b6f9-c5f946fcf821/WLS200s-197_2025-02-17_16-51-32_vad_469_50mTP.nc.gz)
