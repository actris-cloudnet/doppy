# Changelog

## 0.5.5 – 2025-07-17

- Read range measurement formula dynamically for overlapping scan

## 0.5.4 – 2025-03-25

- Add wls77 raw parser

## 0.5.3 – 2025-03-12

- Add a range formula

## 0.5.2 – 2025-03-05

- Fix typehints

## 0.5.1 – 2025-03-05

- Add netcdf time axis attribute

## 0.5.0 – 2025-03-04

- Add turbulence product
- Add netcdf4 classic support
- Improved velocity mask

## 0.4.2 – 2024-12-11

- Rename sys params names to follow cf conventions

## 0.4.1 – 2024-12-10

- Fix sys params files that have concatenated values

## 0.4.0 – 2024-12-02

- Add windcube stare product

## 0.3.7 – 2024-10-14

- Fix cabauw dbs time reference

## 0.3.6 – 2024-10-09

- Add windcube dbs support for the wind product

## 0.3.5 – 2024-08-30

- Add time_reference to nc units in old windcube files

## 0.3.4 – 2024-08-26

- Ignore parsing errors while reading multiple halo bg files
- Ignore masks from wls200s

## 0.3.3 – 2024-08-22

- Add product netcdf writers

## 0.3.2 – 2024-08-22

- add beta cross signal to StareDepol product

## 0.3.1 – 2024-08-15

- Increase tolerance when checking co and cross values

## 0.3.0 – 2024-08-14

- Add depolarisation product
- Support context manager in `doppy.netcdf.Dataset`

## 0.2.4 – 2024-07-25

- Deprecate `add_atribute`. Use `add_attribute` instead.

## 0.2.3 – 2024-06-13

- Add support for older data format

## 0.2.2 – 2024-05-28

- Add azimuth offset for wind product

## 0.2.1 – 2024-05-07

- Include system ID in products

## 0.2.0 – 2024-05-06

- Add wls70 wind product
- Handle non-overlapping data and background files

## 0.1.4 – 2024-04-23

- Remove nan profiles

## 0.1.3 – 2024-03-20

- Fix netcdf time unit

## 0.1.2 – 2024-03-20

- Fix fillvalue

## 0.1.1 – 2024-03-15

- Exclude small elevation angles in wind product

## 0.1.0 – 2024-02-21

- Add wind product from windcube

## 0.0.7 – 2024-02-15

- Fix issue causing headers to be unmergeable

## 0.0.4 – 2024-02-14

- Add wind product

## 0.0.3 – 2024-02-09

- Allow small offset for the stare elevation angle
- Skip bg clustering if only one bg profile
