from pathlib import Path

import doppy

from tests import utils
from tests.utils import Testcase, TestType, testfiles_to_paths


def run_tests():
    path = Path(__file__).parent / "tests.toml"
    tests = utils.parse_tests_toml(path)
    for tcase in tests.testcase:
        match tcase.type:
            case TestType.Wind:
                test_wind(tcase)


def test_wind(testcase: Testcase):
    paths = testfiles_to_paths(testcase.files)
    wind = doppy.product.Wind.from_halo_data(paths)
    print(wind)


if __name__ == "__main__":
    run_tests()
