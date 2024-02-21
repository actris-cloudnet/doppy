import os

import pytest


@pytest.fixture
def cache():
    return "GITHUB_ACTIONS" not in os.environ
