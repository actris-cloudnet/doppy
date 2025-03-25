from pathlib import Path

import doppy

src = Path("data") / "wls77" / "WLS77344_2024_12_17__12_02_01.rtd"

raw = doppy.raw.Wls77.from_src(src)
