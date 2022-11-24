import pytest
import json
import logging

from smartbox_monopy.biosticker.config import BiostickerConfigParser
from smartbox_monopy.biosticker.asynchandler import BiostickerBLEHandler

from .setup_tests import demo_json_configfile

def test_biosticker_config(demo_json_configfile):
    logger = logging.getLogger(
        'dummy_logger').addHandler(logging.NullHandler())
    config_file = BiostickerConfigParser(demo_json_configfile, logger)
