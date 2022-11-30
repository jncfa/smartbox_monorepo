

# the mqtt client handles the MQTT broker requests, and handles the data transformation into MQTT transmissions
# Version 1.0

import random
import time
from datetime import datetime, timedelta
import ssl
import json
import sys
import time
import threading

import asyncio
import asyncio_mqtt as aiomqtt
import logging

import numpy as np

from smartbox_monopy.processing.queueitem import *

import os

from .options import MQTTOptionsParser
from typing import Union, NamedTuple, Callable, Coroutine, List

from smartbox_monopy.biosticker.asynchandler import IMUData, ECGTimestampedData


class MQTTClientHandler():
    class _MQTTSensorInfo(NamedTuple):
        publish_topic: str

    class _MQTTQueueMessageStruct(NamedTuple):
        publish_topic: str
        payload: str

    PUBLISH_TOPIC_ENTRY = 'PUB_ENTRY'

    def __init__(self, config, db_handler):

        self.logger = logging.getLogger("mqtt")
        self.config = MQTTOptionsParser(config, self.logger)
        self.db_handler = db_handler
        self.signal_disconnect = False

        # MQTT Client is initialized via context manager, so we need to be careful handling this
        # We're handling this via an internal queue in which we "push" messages to be sent
        self.is_connected: bool = False
        self._inner_message_queue: asyncio.Queue[MQTTClientHandler._MQTTQueueMessageStruct] = asyncio.Queue(
            maxsize=1)
        #self._mqtt_client: Union[aiomqtt.Client, None] = None

    async def publish_ecg_data(self, data: List[ECGTimestampedData], timestamp: datetime):
        self.logger.debug(f"Publishing ECG data...")
        if (self.is_connected):
            # build payload
            for ecg_data, timestamp in data:
                payload = {
                    "client_id": str(self.config.client_uuid),
                    "timestamp": timestamp.timestamp(),
                    "message_type": self.config.event_message_type_map[QueueEvent.ECG_SENSOR_EVENT],
                    "payload": {"bpm": ecg_data}
                }
                await self._inner_message_queue.put(MQTTClientHandler._MQTTQueueMessageStruct(self.config.event_topic_map[QueueEvent.ECG_SENSOR_EVENT], json.dumps(payload)))
        else:
            self.logger.warning(
                f"Client is not connected, discarding message...")

    async def publish_imu_data(self, data: IMUData, timestamp: datetime):
        self.logger.debug(f"Publishing IMU data...")
        if (self.is_connected):
            # build payload

            payload = {
                "client_id": str(self.config.client_uuid),
                "timestamp": timestamp.timestamp(),
                "message_type": self.config.event_message_type_map[QueueEvent.IMU_SENSOR_EVENT],
                "payload": {
                    "imu": {
                        "linear_acceleration": {
                            "x": data.imu_vector[0],
                            "y": data.imu_vector[1],
                            "z": data.imu_vector[2]
                        }, "angular_velocity": {
                            "x": data.imu_vector[3],
                            "y": data.imu_vector[4],
                            "z": data.imu_vector[5]}
                    }, "pose_description": data.pose_description
                }
            }

            await self._inner_message_queue.put(MQTTClientHandler._MQTTQueueMessageStruct(self.config.event_topic_map[QueueEvent.IMU_SENSOR_EVENT], json.dumps(payload)))
        else:
            self.logger.warning(
                f"Client is not connected, discarding message...")

    async def publish_rr_data(self, data: int, timestamp: datetime):
        self.logger.debug(f"Publishing Respiration data...")
        if (self.is_connected):
            # build payload

            payload = {
                "client_id": str(self.config.client_uuid),
                "timestamp": timestamp.timestamp(),
                "message_type": self.config.event_message_type_map[QueueEvent.RR_SENSOR_EVENT],
                "payload": {"respiration": data}
            }

            await self._inner_message_queue.put(MQTTClientHandler._MQTTQueueMessageStruct(self.config.event_topic_map[QueueEvent.RR_SENSOR_EVENT], json.dumps(payload)))
        else:
            self.logger.warning(
                f"Client is not connected, discarding message...")

    async def publish_heartrate_data(self, data: int, timestamp: datetime):
        self.logger.debug(f"Publishing Respiration data...")
        if (self.is_connected):
            # build payload

            payload = {
                "client_id": str(self.config.client_uuid),
                "timestamp": timestamp.timestamp(),
                "message_type": self.config.event_message_type_map[QueueEvent.HEARTRATE_SENSOR_EVENT],
                "payload": {"bpm": data}
            }

            await self._inner_message_queue.put(MQTTClientHandler._MQTTQueueMessageStruct(self.config.event_topic_map[QueueEvent.HEARTRATE_SENSOR_EVENT], json.dumps(payload)))
        else:
            self.logger.warning(
                f"Client is not connected, discarding message...")

    async def publish_temperature_data(self, data: float, timestamp: datetime):
        self.logger.debug(f"Publishing Temperature data...")
        if (self.is_connected):
            # build payload

            payload = {
                "client_id": str(self.config.client_uuid),
                "timestamp": timestamp.timestamp(),
                "message_type": self.config.event_message_type_map[QueueEvent.TEMPERATURE_SENSOR_EVENT],
                "payload": {"temperature": data, "is_celsius": True}
            }

            await self._inner_message_queue.put(MQTTClientHandler._MQTTQueueMessageStruct(self.config.event_topic_map[QueueEvent.TEMPERATURE_SENSOR_EVENT], json.dumps(payload)))
        else:
            self.logger.warning(
                f"Client is not connected, discarding message...")

    async def publish_spo2_data(self, data: int, timestamp: datetime):
        self.logger.debug(f"Publishing SPO2 data...")
        if (self.is_connected):
            # build payload

            payload = {
                "client_id": str(self.config.client_uuid),
                "timestamp": timestamp.timestamp(),
                "message_type": self.config.event_message_type_map[QueueEvent.SPO2_SENSOR_EVENT],
                "payload": {"spo2": data}
            }

            await self._inner_message_queue.put(MQTTClientHandler._MQTTQueueMessageStruct(self.config.event_topic_map[QueueEvent.SPO2_SENSOR_EVENT], json.dumps(payload)))
        else:
            self.logger.warning(
                f"Client is not connected, discarding message...")

    def reset(self):
        self.signal_disconnect = False
        pass

    async def _publish_worker(self, mqtt_client: aiomqtt.Client, worker_id: int = 1):
        self.logger.debug(
            f"publish-worker-{worker_id}: Setting up publish worker..")

        while not self.signal_disconnect:
            data = await self._inner_message_queue.get()
            self.logger.debug(
                f"Publishing message on topic {data.publish_topic}...")
            await mqtt_client.publish(data.publish_topic, payload=data.payload)

    async def _sync_handler_worker(self, mqtt_client: aiomqtt.Client, worker_id: int = 1):
        self.logger.debug(f"sync-worker-{worker_id}: Setting up sync worker..")

        while not self.signal_disconnect:
            async with mqtt_client.filtered_messages(self.config.event_topic_map[QueueEvent.MQTT_SYNC_REQ_EVENT]) as sync_messages:
                await mqtt_client.subscribe(self.config.event_topic_map[QueueEvent.MQTT_SYNC_REQ_EVENT])
                async for message in sync_messages:
                    print(message.topic)
                    print(json.loads(message.payload))
        self.logger.debug(f"sync-worker-{worker_id}: Stopping worker...")

    async def spin(self):
        if self.config.disable_mqtt:
            self.logger.info(
                f"MQTT is disabled in the configuration file, so no communication will be handled, silently ignoring MQTT requests")

            # removing handlers since we're not doing anything with MQTT
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)
            self.logger.addHandler(logging.NullHandler())
            
        else:    
            # reset state on spin
            self.reset()
            self.logger.info(
                f"Connecting to remote broker...")
            while not self.signal_disconnect:
                self.is_connected = False
                try:
                    async with aiomqtt.Client(self.config.host, tls_params=self.config.tls_config, client_id=str(self.config.client_uuid), logger=self.logger) as mqtt_client:
                        self.is_connected = True

                        await asyncio.gather(
                            self._publish_worker(mqtt_client),
                            self._sync_handler_worker(mqtt_client)
                        )
                        print("stopped working?")

                except aiomqtt.MqttError as error:
                    self.logger.exception(
                        f'Error "{error}". Reconnecting in {self.config.reconnect_interval} seconds.')

                except Exception as exc:
                    self.logger.exception(
                        f'Unknown exception detected. Reconnecting in {self.config.reconnect_interval} seconds.')

                finally:
                    self.is_connected = False
                    await asyncio.sleep(self.config.reconnect_interval)
