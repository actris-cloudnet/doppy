"""Profile helper: runs stare processing under cProfile.

Usage: python -m tests.helpers.profile_helper '<json>' '<output.prof>'

Input JSON: same format as bench_helper
Output: .prof file at the specified path
"""

import cProfile
import json
import sys

from tests.helpers.bench_helper import bench_stare


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python -m tests.helpers.profile_helper '<json>' '<output.prof>'",
            file=sys.stderr,
        )
        sys.exit(1)

    case = json.loads(sys.argv[1])
    output_path = sys.argv[2]

    product_type = case["product"]
    if product_type != "stare":
        print(
            f"Unsupported product for profiling: {product_type}",
            file=sys.stderr,
        )
        sys.exit(1)

    profiler = cProfile.Profile()
    profiler.enable()
    bench_stare(case)
    profiler.disable()
    profiler.dump_stats(output_path)

    print(f"Profile saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
