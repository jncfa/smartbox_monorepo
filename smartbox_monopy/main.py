import asyncio
import bleak
import json
import logging
import logging.config
import time

from smartbox_monopy.biosticker.asynchandler import BiostickerBLEHandler
from smartbox_monopy.oximeter.asynchandler import OximeterBLEHandler


async def consumer_dist(queue: asyncio.Queue):
    """Code which consumes the queue, by issuing commands to both MQTT and the DB handler."""

    while True:
        data = await queue.get()  # wait for data to be processed

        # 


async def main(config):
    # TODO: check if we need to set a maxsize to force .get to be executed earlier
    data_queue = asyncio.Queue()


    # setup every coroutine to run
    # BLE: Biosticker, Oximeter
    # DB: MongoDBConsumer
    # MQTT: MQTTClientConsumer

    biosticker_handler = BiostickerBLEHandler()

    # Spin up the producers and consumers
    await asyncio.gather(
        connect_to_biosticker(config),
        connect_to_oximeter(config)
    )

if __name__ == "__main__":
    # TODO: Check if we need to change the logger to process data in a seperate thread
    logging.config.fileConfig('logging.config')
    config = None

    with open('config.json') as f:
        config = json.load(f)

    asyncio.run(main(config), debug=True)
