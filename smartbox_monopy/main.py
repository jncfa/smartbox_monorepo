import asyncio
import bleak
import json
import logging
import logging.config
import time
import queue
import signal
import functools

from smartbox_monopy.biosticker.asynchandler import BiostickerBLEHandler
from smartbox_monopy.oximeter.asynchandler import OximeterBLEHandler
from smartbox_monopy.db.asynchandler import MongoDBHandler
from smartbox_monopy.mqtt.asynchandler import MQTTClientHandler
from smartbox_monopy.processing.dataconsumerfactory import DataConsumerFactory

DEBUG_MODE_ENTRY="DEBUG"

# sig handler to safely keyboardinterrupt
async def signal_handler(signo, loop):
    print("Detected user interruption, shutting down..")
    for task in asyncio.Task.all_tasks():
        if task is asyncio.tasks.Task.current_task():
            continue
        task.cancel()

def entrypoint():
    try:
        # TODO: Check if we need to change the logger to process data in a seperate thread
        logging.config.fileConfig('logging.config')

        config = None
        with open('config.json') as f:
            config = json.load(f)

        logger = logging.getLogger("main")
        logger.info("Starting up...")

        loop = asyncio.get_event_loop()
    
        for signo in [signal.SIGINT, signal.SIGTERM]:
            func = functools.partial(asyncio.ensure_future, signal_handler(signo, loop))
            loop.add_signal_handler(signo, func)

        if (config[DEBUG_MODE_ENTRY] == True):
            loop.set_debug(True)
        else:
            loop.set_debug(False)


        # setup every coroutine to run
        # BLE: Biosticker, Oximeter [DONE]
        # DB: MongoDBConsumer
        # MQTT: MQTTClientConsumer
        
        # TODO: After setting up the MQTT client, use "pair_request"
        # to indicate which biosticker is being used
        
        data_queue = asyncio.Queue(maxsize=1, loop=loop)
        
        # producers
        biosticker_handler = BiostickerBLEHandler(config, data_queue)
        oximeter_handler = OximeterBLEHandler(config, data_queue)

        # consumers
        mqtt_handler = None
        db_handler = MongoDBHandler(config)
        #mqtt_handler = MQTTClientHandler(config, db_handler)
        data_consumer_factory = DataConsumerFactory(config, data_queue, mqtt_handler, db_handler)

        logger.info("Sending pair requests to the broker...")

        # Send
        #await mqtt_handler.publish_pair_request(self.biosticker_handler.config.mac_address)
        #await mqtt_handler.publish_pair_request(self.oximeter_handler.config.mac_address)

        logger.info("Coroutines setup, spinning up tasks...")
        loop.run_until_complete(asyncio.gather(
            # producers
            biosticker_handler.spin(),
            oximeter_handler.spin(),

            # consumers / workers
            *data_consumer_factory.spawn_workers(),
            return_exceptions=False
        ))

    except asyncio.exceptions.CancelledError:
        pass
    except KeyboardInterrupt:
        pass

    raise SystemExit(0)
    
if __name__ == "__main__":
    entrypoint()
