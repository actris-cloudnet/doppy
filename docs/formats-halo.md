# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
```

## Example files

- [lindenberg](https://hdl.handle.net/21.12132/3.423d89c1b5114af7), [Stare_44_20240721_12.hpl](https://cloudnet.fmi.fi/api/download/raw/4f7f7c2c-2ff1-478b-a133-abb3753feb4b/Stare_44_20240721_12.hpl)
- [juelich](https://hdl.handle.net/21.12132/3.48bd7da035b94ffd), [Stare_17_20240423_18.hpl](https://cloudnet.fmi.fi/api/download/raw/c5ad99ff-1008-405e-8e75-7980a23a3d3e/Stare_17_20240423_18.hpl)
- [mindelo](https://hdl.handle.net/21.12132/3.738143791c524103), [Stare_166_20230204_20.hpl](https://cloudnet.fmi.fi/api/download/raw/3553a4de-57b6-4254-82c7-4490a3e2798d/Stare_166_20230204_20.hpl)
- [eriswil](https://hdl.handle.net/21.12132/3.be50699171b24e17), [Stare_91_20230216_11.hpl](https://cloudnet.fmi.fi/api/download/raw/531d948d-e47b-4f27-81f0-68829b93d862/Stare_91_20230216_11.hpl)
- [warsaw](https://hdl.handle.net/21.12132/3.c8231fca052b4baa), [Stare_213_20211002_06.hpl](https://cloudnet.fmi.fi/api/download/raw/e0cca0f3-307b-4c98-a6fb-c600d068b50b/Stare_213_20211002_06.hpl)
- [punta-arenas](https://hdl.handle.net/21.12132/3.be50699171b24e17), [Stare_91_20190903_20.hpl](https://cloudnet.fmi.fi/api/download/raw/e8f44362-fb3b-4eaa-bfed-032f7847d0c8/Stare_91_20190903_20.hpl)
- [leipzig](https://hdl.handle.net/21.12132/3.be50699171b24e17), [Stare_91_20230530_00.hpl](https://cloudnet.fmi.fi/api/download/raw/1f6170bd-1733-4185-bee1-2825c673cd40/Stare_91_20230530_00.hpl)
- [hyytiala](https://hdl.handle.net/21.12132/3.421272f219be4f97), [Stare_46_20221225_07.hpl](https://cloudnet.fmi.fi/api/download/raw/fd5c366e-612d-42ad-aa4c-ad1d8c20a479/Stare_46_20221225_07.hpl)
- [chilbolton](https://hdl.handle.net/21.12132/3.1e2e7ddeeda641e5), [Stare_118_20201227_14.hpl](https://cloudnet.fmi.fi/api/download/raw/41e374d5-f329-4886-be6b-c648bfbe552b/Stare_118_20201227_14.hpl)
- [kenttarova](https://hdl.handle.net/21.12132/3.a93d1483f10742ff), [Stare_146_20231205_15.hpl](https://cloudnet.fmi.fi/api/download/raw/069f9d13-4b43-4b3b-a59e-d8623308dcdc/Stare_146_20231205_15.hpl)
- [vehmasmaki](https://hdl.handle.net/21.12132/3.af519eeea2db4a90), [Stare_53_20210406_06.hpl](https://cloudnet.fmi.fi/api/download/raw/77a7e752-1e2c-473f-9991-fc059fba49c0/Stare_53_20210406_06.hpl)
- [bucharest](https://hdl.handle.net/21.12132/3.db58480f58ca49ad), [Stare_158_20240930_09.hpl](https://cloudnet.fmi.fi/api/download/raw/8872909b-8d62-4c2d-8ed2-028652edb534/Stare_158_20240930_09.hpl)
- [granada](https://hdl.handle.net/21.12132/3.eadafa59ffa648de), [Stare_102_20181125_10.hpl](https://cloudnet.fmi.fi/api/download/raw/92cde6b1-345e-4ee7-9dd0-4e4f6109f9b6/Stare_102_20181125_10.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****

```

## Example files

- [granada](https://hdl.handle.net/21.12132/3.1d227f1b12b04efc), [Stare_258_20230603_17.hpl](https://cloudnet.fmi.fi/api/download/raw/b1aec8a5-5689-4d7c-8243-043272b0580e/Stare_258_20230603_17.hpl)
- [granada](https://hdl.handle.net/21.12132/3.eadafa59ffa648de), [Stare_102_20210909_19.hpl](https://cloudnet.fmi.fi/api/download/raw/831cf6b5-f815-457c-8fa3-bbfb6f5d681d/Stare_102_20210909_19.hpl)
- [hyytiala](https://hdl.handle.net/21.12132/3.421272f219be4f97), [User1_46_20221226_004641.hpl](https://cloudnet.fmi.fi/api/download/raw/f758f1be-8ed1-455d-90a3-cdba97b12f5b/User1_46_20221226_004641.hpl)
- [limassol](https://hdl.handle.net/21.12132/3.a5e937a2d7e64283), [Stare_253_20241118_15.hpl](https://cloudnet.fmi.fi/api/download/raw/a2ee9e5f-6523-48b4-850d-eb14a34dd229/Stare_253_20241118_15.hpl)
- [cluj](https://hdl.handle.net/21.12132/3.5d15cd3ce9c54139), [Stare_271_20240622_03.hpl](https://cloudnet.fmi.fi/api/download/raw/5643ef57-099f-4a8f-b525-424e0c445705/Stare_271_20240622_03.hpl)
- [leipzig](https://hdl.handle.net/21.12132/3.f6f3cee4a8014f41), [Stare_232_20240606_09.hpl](https://cloudnet.fmi.fi/api/download/raw/9408b629-4044-487c-9cff-ae410c553e54/Stare_232_20240606_09.hpl)
- [eriswil](https://hdl.handle.net/21.12132/3.f6f3cee4a8014f41), [Stare_232_20240120_08.hpl](https://cloudnet.fmi.fi/api/download/raw/0a4c7382-7e35-4b15-8b08-3195761360e2/Stare_232_20240120_08.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1) Spectral Width
i3,1x,f6.4,1x,f8.6,1x,e12.6,1x,f6.4 - repeat for no. gates
**** Instrument spectral width = <POS_FLOAT>
```

## Example files

- [neumayer](https://hdl.handle.net/21.12132/3.e166bb0b5e9246ce), [Stare_234_20240626_11.hpl](https://cloudnet.fmi.fi/api/download/raw/ea495955-cf58-43b4-9b4d-36d46ad10914/Stare_234_20240626_11.hpl)
- [warsaw](https://hdl.handle.net/21.12132/3.c8231fca052b4baa), [Stare_213_20240917_13.hpl](https://cloudnet.fmi.fi/api/download/raw/1eb563d1-db23-4d1b-8126-3f3a12920380/Stare_213_20240917_13.hpl)
- [soverato](https://hdl.handle.net/21.12132/3.31a1d1e9694f47bd), [Stare_194_20210711_17.hpl](https://cloudnet.fmi.fi/api/download/raw/d57e30b0-614b-442f-8522-59b35e06c42e/Stare_194_20210711_17.hpl)
- [potenza](https://hdl.handle.net/21.12132/3.31a1d1e9694f47bd), [Stare_194_20240222_11.hpl](https://cloudnet.fmi.fi/api/download/raw/acf5336b-a2b6-4250-9e1b-1c76062c1779/Stare_194_20240222_11.hpl)
- [lindenberg](https://hdl.handle.net/21.12132/3.4b31c245e3b143f0), [Stare_288_20240916_00.hpl](https://cloudnet.fmi.fi/api/download/raw/68d695b6-5922-4d06-92cc-7fc93772755a/Stare_288_20240916_00.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
```

## Example files

- [hyytiala](https://hdl.handle.net/21.12132/3.421272f219be4f97), [Stare_46_20230318_14.hpl](https://cloudnet.fmi.fi/api/download/raw/f243bb40-315d-49ff-b8a8-bae7448dfeb8/Stare_46_20230318_14.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of waypoints in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
**** Instrument spectral width = <POS_FLOAT>
```

## Example files

- [warsaw](https://hdl.handle.net/21.12132/3.c8231fca052b4baa), [User5_213_20230628_014615.hpl](https://cloudnet.fmi.fi/api/download/raw/4f2f77fc-6485-4b52-a74d-65bcef6d3d86/User5_213_20230628_014615.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
**** Instrument spectral width = <POS_FLOAT>
```

## Example files

- [warsaw](https://hdl.handle.net/21.12132/3.c8231fca052b4baa), [Stare_213_20220429_09.hpl](https://cloudnet.fmi.fi/api/download/raw/fd88f815-714a-4174-a3b2-1fda5bd04466/Stare_213_20220429_09.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of waypoints in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
```

## Example files

[granada](https://hdl.handle.net/21.12132/3.1d227f1b12b04efc), [User3_258_20230409_085717.hpl](https://cloudnet.fmi.fi/api/download/raw/17f48eb8-d9ec-4f11-971b-e24a2baf4bee/User3_258_20230409_085717.hpl)

## Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT_COMMA_SEPARATED>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS,FF>
Resolution (m/s):	<POS_FLOAT_COMMA_SEPARATED>
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
```

## Example files

- [granada](https://hdl.handle.net/21.12132/3.1d227f1b12b04efc), [Stare_258_20230207_14.hpl](https://cloudnet.fmi.fi/api/download/raw/7012178c-ec3b-4609-8f86-504e2f201bed/Stare_258_20230207_14.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of waypoints in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Range of measurement (center of gate) = Gate length / 2 + (range gate x 3)
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
```

## Example files

- [granada](https://hdl.handle.net/21.12132/3.1d227f1b12b04efc), [User1_258_20230308_145351.hpl](https://cloudnet.fmi.fi/api/download/raw/a63cb07b-4634-4477-bfcf-67a20fc2a433/User1_258_20230308_145351.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS.FF>
Resolution (m/s):	<POS_FLOAT>
Range of measurement (center of gate) = Gate length / 2 + (range gate x 3)
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
```

## Example files

- [cluj](https://hdl.handle.net/21.12132/3.5d15cd3ce9c54139), [Stare_271_20240924_23.hpl](https://cloudnet.fmi.fi/api/download/raw/dd615e89-c53a-4536-9c77-57284268bf40/Stare_271_20240924_23.hpl)

# Format

```
Filename:	<FILENAME>
SYSTEM ID:	<POS_INT>
Number of gates:	<POS_INT>
Range gate length (m):	<POS_FLOAT_COMMA_SEPARATED>
Gate length (pts):	<POS_INT>
Pulses/ray:	<POS_INT>
No. of rays in file:	<POS_INT>
Scan type:	<SCAN_TYPE>
Focus range:	<POS_INT>
Start time:	<TIME_FORMAT YYYYMMDD HH:MM:SS,FF>
Resolution (m/s):	<POS_FLOAT_COMMA_SEPARATED>
Range of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1) Spectral Width
i3,1x,f6.4,1x,f8.6,1x,e12.6,1x,f6.4 - repeat for no. gates
**** Instrument spectral width = <POS_FLOAT_COMMA_SEPARATED>
```

## Example files

- [potenza](https://hdl.handle.net/21.12132/3.31a1d1e9694f47bd), [Stare_194_20231213_15.hpl](https://cloudnet.fmi.fi/api/download/raw/d164db1e-b5eb-4da4-9aa2-4161f5bb7c08/Stare_194_20231213_15.hpl)
