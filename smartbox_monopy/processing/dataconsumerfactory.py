import asyncio
import smartbox_monopy.db.asynchandler as db
import smartbox_monopy.mqtt.asynchandler as mqtt

import logging
from .queueitem import *

from smartbox_monopy.biosticker.options import BiostickerOptionsParser
from smartbox_monopy.oximeter.options import OximeterOptionsParser


class DataConsumerFactory:
    def __init__(self, config: dict, data_queue: asyncio.Queue, mqtt_client: mqtt.MQTTClientHandler, db: db.MongoDBHandler, worker_count = 10) -> None:
        self.mqtt_client = mqtt_client
        self.db = db
        self.data_queue = data_queue
        self.worker_count = worker_count

    async def _worker_task(self, worker_id):
        logger = logging.getLogger(f"worker-{worker_id}")

        logger.info(f"Initialized worker.")

        while True:
            id, timestamp, data = await self.data_queue.get()
            logger.debug(f"running in worker task {id=}, {timestamp=}, {data=}")

            if (id == ECG_SENSOR_EVENT):
                await self.db.insert_ecg_data(data, timestamp)
                #await self.mqtt_client.publish_ecg_data(data, timestamp)
            elif (id == IMU_SENSOR_EVENT):
                await self.db.insert_imu_data(data, timestamp)
                #await self.mqtt_client.publish_imu_data(data, timestamp)
            elif (id == RR_SENSOR_EVENT):
                await self.db.insert_rr_data(data, timestamp)
                #await self.mqtt_client.publish_rr_data(data, timestamp)
            elif (id == BATTERY_SENSOR_EVENT):
                await self.db.insert_battery_data(data, timestamp)
                #await self.mqtt_client.publish_battery_data(data, timestamp)
            elif (id == HEARTRATE_SENSOR_EVENT):
                await self.db.insert_heartrate_data(data, timestamp)
                #await self.mqtt_client.publish_battery_data(data, timestamp)
            elif (id == TEMPERATURE_SENSOR_EVENT):
                await self.db.insert_temperature_data(data, timestamp)
                #await self.mqtt_client.publish_temperature_data(data, timestamp)
            elif (id == SPO2_SENSOR_EVENT):
                await self.db.insert_spo2_data(data, timestamp)
                #await self.mqtt_client.publish_spo2_data(data, timestamp)          
            elif (id == PR_SENSOR_EVENT):
                await self.db.insert_pulserate_data(data, timestamp)

    def spawn_workers(self):
        # return list of workers to await
        return [
           self._worker_task(worker_id) for worker_id in range(1, self.worker_count+1)
        ]