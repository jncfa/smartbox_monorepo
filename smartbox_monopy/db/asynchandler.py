

import motor.motor_asyncio
import pprint
import datetime
import time
import logging
from typing import Any

from .options import MongoDbOptionsParser

class MongoDBHandler():

    def __init__(self, config: dict):
        self.logger = logging.getLogger('database')
        self.config = MongoDbOptionsParser(config, logger=self.logger)
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(self.config.hostname)

        # Create the database
        smartbox_database = client['smartbox_database']

        #Sensors collection
        self.sensors_collection = smartbox_database.sensors_collection
        self.sensors_collection_imu = smartbox_database.sensors_collection_imu
    
    async def insert_imu_data(self, data, timestamp):
        await self.insert_sensors_collection_imu(timestamp, *data.imu_vector)

    async def insert_ecg_data(self, data, timestamp):
        # this contains multiple points
        for data_point, data_ts in data:
            await self.insert_sensors_collection('ECG', data_point, data_ts)

    async def insert_rr_data(self, data, timestamp):
        await self.insert_sensors_collection('Respiratory Rate', data, timestamp)
    
    async def insert_rr1_data(self, data, timestamp):
        await self.insert_sensors_collection('Respiratory Sensor 1', data, timestamp)

    async def insert_rr2_data(self, data, timestamp):
        await self.insert_sensors_collection('Respiratory Sensor 2', data, timestamp)

    async def insert_heartrate_data(self, data, timestamp):
        await self.insert_sensors_collection('Heart Rate', data, timestamp)

    async def insert_temperature_data(self, data, timestamp):
        await self.insert_sensors_collection('Temperature', data, timestamp)
        
    async def insert_battery_data(self, data, timestamp):
        await self.insert_sensors_collection('Battery Level', data, timestamp)

    async def insert_spo2_data(self, data, timestamp):
        await self.insert_sensors_collection('Oxygen Saturation', data, timestamp)

    async def insert_pulserate_data(self, data, timestamp):
        await self.insert_sensors_collection('Pulse Rate', data, timestamp)

    # Function to insert every sensor measurement in the database but IMU
    async def insert_sensors_collection(self, sensor_name, value: Any, timestamp: datetime.datetime):
        try:       
            sensor = {
                'name': sensor_name,
                'value': value,
                'timestamp': timestamp
            }

            result = await self.sensors_collection.insert_one(sensor)
            self.logger.debug(f'Sensor Added. The sensor Id is {result.inserted_id}')
        except Exception:
            self.logger.exception('Caught exception')
        
    # Function to insert IMU measurements in the database
    async def insert_sensors_collection_imu(self, timestamp, x_linear_acceleration, y_linear_acceleration, z_linear_acceleration, x_angular_acceleration, y_angular_acceleration, z_angular_acceleration):
        try:   
            sensor = {
                'name': 'IMU',
                'value_acc_x': x_linear_acceleration,
                'value_acc_y': y_linear_acceleration,
                'value_acc_z': z_linear_acceleration,
                'value_gyr_x': x_angular_acceleration,
                'value_gyr_y': y_angular_acceleration,
                'value_gyr_z': z_angular_acceleration,
                'timestamp': timestamp
            }

            result = await self.sensors_collection_imu.insert_one(sensor)
            self.logger.debug(f'Sensor Added. The sensor Id is {result.inserted_id}')
            # TODO: Process 'result'
        except Exception:
            self.logger.exception('Caught exception')
    # Function to get data to be synchronized with the server
    async def read_sync_values(self, timestamp, timestampinicio):
        item_details= await self.sensors_collection.find({ 'timestamp': { '$gt': timestamp, '$lt':  timestampinicio}})
        item_details_imu= await self.sensors_collection_imu.find({ 'timestamp': { '$gt': timestamp, '$lt':  timestampinicio}})
        return item_details, item_details_imu