import pytest
import json
import logging

from src.biosticker.handler import BiostickerConfigParser


@pytest.fixture
def demo_json_configfile() -> dict:
    with open("tests/demo_file.json") as f:
        return json.load(f)


def test_biosticker_config(demo_json_configfile):
    logger = logging.getLogger(
        'dummy_logger').addHandler(logging.NullHandler())
    config_file = BiostickerConfigParser(demo_json_configfile, logger)
