

# the mqtt client handles the MQTT broker requests, and handles the data transformation into MQTT transmissions
#Version 1.0

import random
import time
from datetime import datetime, timedelta
import ssl, json, sys, time, threading

import asyncio
import asyncio_mqtt as aiomqtt
import logging

import numpy as np

from smartbox_monopy.processing.queueitem import *

import os

from .options import MQTTOptionsParser

class MQTTClientHandler():

    def __init__(self, config, db_handler):
        
        self.logger = logging.getLogger("mqtt")
        self.config = MQTTOptionsParser(config, self.logger)
        self.db_handler = db_handler

        self.signal_disconnect = False

        self.__tls_params = aiomqtt.TLSParameters(
            ca_certs=None,
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS,
            ciphers=None,
        )


        # MQTT Client is initialized via context manager, so we need to be careful handling this
        # We're handling this via an internal queue in which we "push" messages to be sent 
        self.is_connected: bool = False
        self._mqtt_client: aiomqtt.Client = None

    async def publish_ecg_data(self, data, timestamp):
        self.logger.debug(f"Publishing ECG data...")
        if (self.is_connected):
            payload = {}
            self._mqtt_client.publish()
        else:
            self.logger.warning(f"Client is not connected yet")


    async def publish_imu_data(self, data, timestamp):
        self.logger.debug(f"Publishing IMU data...")
        pass

    async def publish_rr_data(self, data, timestamp):
        self.logger.debug(f"Publishing Respiration data...")
        pass

    async def publish_battery_data(self, data, timestamp):
        self.logger.debug(f"Publishing Battery data...")
        pass

    async def publish_temperature_data(self, data, timestamp):
        self.logger.debug(f"Publishing Temperature data...")
        pass

    async def publish_spo2_data(self, data, timestamp):
        self.logger.debug(f"Publishing SPO2 data...")
        pass
    
    def reset(self):
        pass

    async def spin(self):
        # reset state on spin
        self.reset() 

        while not self.signal_disconnect:
            try:
                async with aiomqtt.Client(self.config.hostname, tls_params=self.__tls_params) as client:
                    await client.publish("measurements/humidity", payload=0.38)       
            
            except aiomqtt.MqttError as error:
                self.logger.exception(f'Error "{error}". Reconnecting in {self.config.reconnect_interval} seconds.')
                await asyncio.sleep(self.config.reconnect_interval)
                
            except Exception as exc:
                pass