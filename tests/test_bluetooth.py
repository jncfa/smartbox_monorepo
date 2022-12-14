import pytest
import json
import logging
import asyncio

from smartbox_monopy.biosticker.asynchandler import BiostickerBLEHandler
from smartbox_monopy.oximeter.asynchandler import OximeterBLEHandler

from .setup_tests import demo_json_configfile


async def sleep_and_shutdown(biosticker_handler:BiostickerBLEHandler, oximeter_handler:OximeterBLEHandler, timeout:float = 60):
    # sleep for a bit
    await asyncio.sleep(timeout)

    # then issue the close connection requests
    await biosticker_handler.close_connection()
    await oximeter_handler.close_connection()

def test_simul_connection(demo_json_configfile):
    # initialize BLE handlers
    biosticker_handler = BiostickerBLEHandler(demo_json_configfile)
    oximeter_handler = OximeterBLEHandler(demo_json_configfile)

    # spin up the handlers and wait a bit to issue a shutdown, if everything worked fine
    asyncio.gather(
        biosticker_handler.spin(),
        oximeter_handler.spin(),
        sleep_and_shutdown(biosticker_handler, oximeter_handler)
    )
    