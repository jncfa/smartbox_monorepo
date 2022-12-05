import json
import pytest

@pytest.fixture
def demo_json_configfile() -> dict:
    with open("tests/demo_file.json") as f:
        return json.load(f)