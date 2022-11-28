import asyncio
import logging
import logging.config
import time
from datetime import datetime as dt
from typing_extensions import final
from termcolor import colored
from .options import OximeterOptionsParser
import libscrc


import bleak
from bleak.backends.characteristic import BleakGATTCharacteristic

from smartbox_monopy.processing.queueitem import *

@final
class OximeterBLEHandler():
    """
    
    """
    def __init__(self, config: dict, data_queue: asyncio.Queue) -> None:
        self.data_queue = data_queue
        self._last_timestamps = {}
        self.logger = logging.getLogger("oximeter")
        self.options = OximeterOptionsParser(config, self.logger)
        self.signal_disconnect = False
        self._stream_data = bytearray()
        # make a lookup table to get the sensor_id mappings 
        self.sensor_id_lookup = {
            sensor_value.uuid: sensor_id
            for sensor_id, sensor_value in self.options.sensors.items() 
        }

        # make a lookup table to map the callbacks to each sensor, using the sensor_id 
        if self.options.oximeter_type == OximeterOptionsParser.BIOSTICKER_TYPE_BLUE:
            self.callback_map = {
                OximeterOptionsParser.PRSPO2_SENSOR_ENTRY: self.handle_data_prspo2_blue
            }
        else:
            self.callback_map = {
                OximeterOptionsParser.PRSPO2_SENSOR_ENTRY: self.handle_data_prspo2_black
            }
    
    def _debug_display_time(self, sensor_id:str):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self._last_timestamps.get(sensor_id, None)
        if (old_timestamp is not None): # ignore first fail
            time_ms = (new_timestamp -old_timestamp)/1e6
            expected_ms = self.options.sensors[sensor_id].period
            self.logger.debug(colored(f'{sensor_id}: took {time_ms} ms', "green" if (abs((time_ms - expected_ms) / expected_ms) < 0.5) else "red"))

        self._last_timestamps[sensor_id] = new_timestamp

    async def handle_data_prspo2_black(self, char: BleakGATTCharacteristic, data: bytearray):
        data_timestamp = dt.now()
        try:
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])
            
            if(data[0] == 254 and data[1] == 10):
                # Get Oxygen & Heartrate
                readable_value_spo2=data[5]
                readable_value_pr=data[4]

                await self.data_queue.put(QueueItem(PR_SENSOR_EVENT,
                    data_timestamp,
                    readable_value_pr))

                await self.data_queue.put(QueueItem(SPO2_SENSOR_EVENT,
                    data_timestamp,
                    readable_value_spo2))
            else:
                self.logger.error("Data does not conform to the expected value")
        except Exception:
            self.logger.exception("Caught unknown exception")
            raise
    async def handle_data_prspo2_blue(self, char: BleakGATTCharacteristic, data: bytearray):
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])
            
            self._stream_data.extend(bytearray(data))
            
            while(True):
                if(len(self._stream_data) == 0):
                    break
                # search for sync sequence
                idx = self._stream_data.find(b'\xaa\x55')
                # gather more bytes if the sync sequence not found
                if(idx < 0):
                    break
                # check if there are enough bytes to read the message length
                # otherwise skip and gather more bytes
                if(len(self._stream_data) >= idx + 4):
                    length = self._stream_data[idx + 3]
                    # check whether all the bytes of the message available
                    # otherwise skip and gather more bytes
                    if(len(self._stream_data) >= idx + 4 + length):
                        # remove the bytes from the self._stream_data prior sync
                        # (if any - as this should not happen except in case of the firs message)
                        del self._stream_data[0 : idx]
                        # copy the whole message 
                        message = self._stream_data[0 : idx + 4 + length]
                        # the last byte of the message is a CRC8/MAXIM 
                        # the CRC sum for the whole message (including the CRC) must be 0
                        if(libscrc.maxim8(message) != 0):
                            self.logger.error("CRC error")
                        # remove the sync bytes and the CRC
                        message =  message[2 : idx + 3 + length]
                        # remove the processed bytes from the self._stream_data
                        del self._stream_data[0 : idx + 4 + length]
                        # messages with 0x08 on the second spot contains values appear on the OLED display
                        if(message[2] == 0x01):
                            if ((message[3] == 0 and message[4] == 0 and message[6] == 0)): # device is still booting
                                pass
                            else:
                                readable_value_spo2=message[3]
                                readable_value_pr=message[4]
                                #readable_value_pi=message[6] / 10 # unused in our code

                                await self.data_queue.put(QueueItem(PR_SENSOR_EVENT,
                                    data_timestamp,
                                    readable_value_pr))

                                await self.data_queue.put(QueueItem(SPO2_SENSOR_EVENT,
                                    data_timestamp,
                                    readable_value_spo2))
                    else:
                        break
                else:
                    break
        except Exception:
            self.logger.exception("Caught unknown exception")
            raise
    
    def reset(self):
        self.signal_disconnect=False
        self._last_timestamps = {}

    async def spin(self):
        # reset state on spin
        self.reset()
        # TODO: Should the devices attempt to pair?
        while not self.signal_disconnect:
            try:
                async with bleak.BleakClient(self.options.mac_address, adapter=self.options.adapter_id, disconnected_callback=self._on_disconnect) as client:
                    self.logger.info("Device connected.")

                    # configure notification on every characteristic
                    for sensor_id, sensor_callback in self.callback_map.items():
                        await client.start_notify(self.options.sensors[sensor_id].uuid, sensor_callback)

                    if (self.options.oximeter_type == OximeterOptionsParser.BIOSTICKER_TYPE_BLUE):
                        await client.write_gatt_char(self.options.flags[OximeterOptionsParser.INIT_FLAG_ENTRY].uuid, bytearray([0x0d]))
                        
                    while (client.is_connected or self.signal_disconnect):
                        await asyncio.sleep(10) # sleep while the client is connected or until something requests to halt the communications
                
                if (self.signal_disconnect):
                    self.logger.info("Device disconnected properly.")
                else:
                    self.logger.info("Device disconnected unexpectedly, trying again...")

            except bleak.exc.BleakDeviceNotFoundError:
                self.logger.error("Device couldn't be found, trying again...")
            
            except bleak.exc.BleakDBusError:
                self.logger.exception("Caught unknown DBus error.")
                raise
            
            except Exception: 
                self.logger.exception("Caught unknown error.")
                raise

    def _on_disconnect(self, client:bleak.BleakClient):
        self.logger.info("Device has disconnected.")
    
    def disconnect(self):
        self.signal_disconnect=True