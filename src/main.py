import asyncio
import bleak
import json
import logging
import logging.config
import time

from biosticker.handler import BiostickerBLEHandler
from oximeter.handler import OximeterBLEHandler

async def main(config):
    await asyncio.gather(
       connect_to_biosticker(config),
       connect_to_oximeter(config)
    )

if __name__ == "__main__":
    logging.config.fileConfig('logging.config')
    config = None

    with open('config.json') as f:
        config = json.load(f)

    asyncio.run(main(config), debug=True)