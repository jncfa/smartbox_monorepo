import pytest
import json
import logging


from smartbox_monopy.oximeter.options import OximeterOptionsParser
from smartbox_monopy.oximeter.asynchandler import OximeterBLEHandler

from .setup_tests import demo_json_configfile

def test_biosticker_config(demo_json_configfile):
    logger = logging.getLogger(
        'dummy_logger').addHandler(logging.NullHandler())
    config_file = OximeterOptionsParser(demo_json_configfile, logger)
