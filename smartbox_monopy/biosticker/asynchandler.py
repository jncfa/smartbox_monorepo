import asyncio
import logging
import time
import math
import struct
from datetime import timedelta, datetime as dt
from typing import final, List

import bleak
from bleak.backends.characteristic import BleakGATTCharacteristic

from smartbox_monopy.vendor.wrapper import RespirationProcessorWrapper
from smartbox_monopy.processing.queueitem import *
from .options import BiostickerOptionsParser


class ECGTimestampedData(NamedTuple):
    data: int
    timestamp: dt


class IMUData(NamedTuple):
    pose_description: str
    imu_vector: List[int]


@final
class BiostickerBLEHandler():
    """

    """

    def __init__(self, options: dict, data_queue: asyncio.Queue) -> None:
        self.data_queue = data_queue
        self._last_timestamps = {}
        self.logger = logging.getLogger("biosticker")
        self.options = BiostickerOptionsParser(options, self.logger)
        self._ecg_last_timestamp = None
        self._resp_wrapper = RespirationProcessorWrapper()

        # make a lookup table to get the sensor_id mappings
        self.sensor_id_lookup = {
            sensor_tuple.uuid: sensor_id
            for sensor_id, sensor_tuple in self.options.sensors.items()
        }

        # make a lookup table to map the callbacks to each sensor, using the sensor_id
        self.callback_map = {
            BiostickerOptionsParser.HEARTRATE_SENSOR_ENTRY: self.handle_data_heart_rate,
            BiostickerOptionsParser.TEMPERATURE_SENSOR_ENTRY: self.handle_data_temperature,
            BiostickerOptionsParser.BATTERY_SENSOR_ENTRY: self.handle_data_battery,
            BiostickerOptionsParser.ECG_SENSOR_ENTRY: self.handle_data_ecg,
            BiostickerOptionsParser.RR1_SENSOR_ENTRY: self.handle_data_rr1,
            BiostickerOptionsParser.RR2_SENSOR_ENTRY: self.handle_data_rr2,
            BiostickerOptionsParser.IMU_SENSOR_ENTRY: self.handle_data_imu,
        }

    def _debug_display_time(self, sensor_id: str) -> None:
        new_timestamp = time.monotonic_ns()
        old_timestamp = self._last_timestamps.get(sensor_id, None)
        if (old_timestamp is not None):  # ignore first fail
            time_ms = (new_timestamp - old_timestamp)/1e6
            expected_ms = self.options.sensors[sensor_id].period

            if (abs((time_ms - expected_ms) / expected_ms) > 0.5):
                self.logger.warning(
                    f'{sensor_id}: took {time_ms}({"+" if (time_ms - expected_ms) > 0 else "-"} {100*(abs(time_ms - expected_ms) / expected_ms)}%) ms')

        self._last_timestamps[sensor_id] = new_timestamp

    def ieee11073_to_float(self, bytestr):
        FIRST_RESERVED_VALUE = 0x007FFFFE
        MDER_NEGATIVE_INFINITY = 0x00800002
        reserved_float_values = [
            math.inf, math.nan, math.nan, math.nan, -math.inf]

        mantissa = int.from_bytes(
            bytestr[0:3], byteorder='little', signed=True)
        expoent = int.from_bytes(bytestr[3:4], byteorder='little', signed=True)

        if (mantissa >= FIRST_RESERVED_VALUE and mantissa <= MDER_NEGATIVE_INFINITY):
            print(mantissa - FIRST_RESERVED_VALUE)
            output = reserved_float_values[mantissa - FIRST_RESERVED_VALUE]
        else:
            output = mantissa * (10.0 ** (expoent))
        
        return output

    async def handle_data_imu(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            # [angular_acc(x,y,z), linear_acc(x,y,z)]
            unpacked_data = list(struct.unpack('ffffff', data))

            # TODO: Add pose description classification
            pose_description = "SITTING"

            await self.data_queue.put(QueueItem(
                QueueEvent.IMU_SENSOR_EVENT,
                data_timestamp,
                IMUData(pose_description, unpacked_data)
            ))
        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    async def handle_data_heart_rate(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            readable_value = int.from_bytes(data, byteorder='big', signed=True)
            await self.data_queue.put(QueueItem(
                QueueEvent.HEARTRATE_SENSOR_EVENT,
                data_timestamp,
                readable_value
            ))
        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    async def handle_data_temperature(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            readable_value = self.ieee11073_to_float(data[1:])
            print(readable_value)
            await self.data_queue.put(QueueItem(
                QueueEvent.TEMPERATURE_SENSOR_EVENT,
                data_timestamp,
                readable_value
            ))

        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    async def handle_data_battery(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            readable_value = int.from_bytes(data, byteorder='big', signed=True)
            await self.data_queue.put(QueueItem(
                QueueEvent.BATTERY_SENSOR_EVENT,
                data_timestamp,
                readable_value
            ))

        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    async def handle_data_rr1(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            readable_value = int.from_bytes(data, byteorder='big', signed=True)
            await self.data_queue.put(QueueItem(
                QueueEvent.RR1_SENSOR_EVENT,
                data_timestamp,
                readable_value
            ))

            if self._resp_wrapper.is_ready():
                # TODO: Their code literally does not work, uncomment the append after fixing
                rpm = await self._resp_wrapper.compute_resp()
                await self.data_queue.put(QueueItem(
                    QueueEvent.RR_SENSOR_EVENT,
                    data_timestamp,
                    rpm
                ))

            #self._resp_wrapper.append_rr1(readable_value, data_timestamp)

        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    async def handle_data_rr2(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            readable_value = int.from_bytes(data, byteorder='big', signed=True)

            await self.data_queue.put(QueueItem(
                QueueEvent.RR2_SENSOR_EVENT,
                data_timestamp,
                readable_value
            ))

            if self._resp_wrapper.is_ready():
                rpm = await self._resp_wrapper.compute_resp()
                await self.data_queue.put(QueueItem(
                    QueueEvent.RR_SENSOR_EVENT,
                    data_timestamp,
                    rpm
                ))

            #self._resp_wrapper.append_rr2(readable_value, data_timestamp)

        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    async def handle_data_ecg(self, char: BleakGATTCharacteristic, data: bytearray) -> None:
        try:
            data_timestamp = dt.now()
            if self.options.debug_mode:
                self._debug_display_time(self.sensor_id_lookup[char.uuid])

            packet_count = data[0]
            timestamp_ecg_aux = self.twos_comp(((data[(2 * packet_count) + 1] << 24) | (data[(2 * packet_count) + 2] << 16) | (
                data[(2 * packet_count) + 3] << 8) | (data[(2 * packet_count) + 4] & 0xFF)), 32)

            timestamp_ecg = data_timestamp
            # we always assume the first message is okay
            if self._ecg_last_timestamp == None:
                self._ecg_last_timestamp = (data_timestamp, timestamp_ecg_aux)
            else:
                # check if packets are missing using the timestamp difference
                time_aux_dif_ms = timestamp_ecg_aux - \
                    self._ecg_last_timestamp[1]

                expected_packet_count = int(time_aux_dif_ms // 7.8)

                if packet_count < expected_packet_count:
                    self.logger.warning(
                        f'Expected {expected_packet_count:d} ECG data points, but only got {packet_count}')
                # edit the timestamp ECG to represent the actual measurement
                timestamp_ecg = self._ecg_last_timestamp[0] + \
                    timedelta(seconds=(time_aux_dif_ms/1000))
                self._ecg_last_timestamp = (timestamp_ecg, timestamp_ecg_aux)

            ecg_timestamped_data: List[ECGTimestampedData] = []
            if packet_count > 1:
                for i in reversed(range(0, data[0])):
                    timestamp_ecg = timestamp_ecg - timedelta(seconds=0.0078)
                    readable_value = (self.twos_comp(
                        ((data[(2 * i) + 1] << 8) | (data[(2 * i) + 2] & 0xFF)), 16))
                    ecg_timestamped_data.append(
                        ECGTimestampedData(readable_value, timestamp_ecg))

            await self.data_queue.put(QueueItem(
                QueueEvent.ECG_SENSOR_EVENT,
                data_timestamp,
                ecg_timestamped_data
            ))

        except Exception:
            self.logger.exception("Caught unknown exception")
            raise

    def _on_disconnect(self, client: bleak.BleakClient) -> None:
        self.logger.info("Device has disconnected.")

    def disconnect(self) -> None:
        self.signal_disconnect = True

    def reset(self) -> None:
        self.signal_disconnect = False
        self._last_timestamps = {}

    async def spin(self) -> None:
        # reset state on spin
        self.reset()

        # TODO: Should the devices attempt to pair as well?
        while not self.signal_disconnect:
            try:
                async with bleak.BleakClient(self.options.mac_address, adapter=self.options.adapter_id, disconnected_callback=self._on_disconnect) as client:
                    self.logger.info("Device connected.")

                    # select emulation mode TODO: help?
                    if self.options.is_sim_biosticker:
                        await client.write_gatt_char(self.options.flags[BiostickerOptionsParser.SELECT_FLAG_ENTRY].uuid, bytearray([0x0A]))
                    else: 
                        await client.write_gatt_char(self.options.flags[BiostickerOptionsParser.SELECT_FLAG_ENTRY].uuid, bytearray([0x0D]))

                    # configure notification on every characteristic
                    for sensor_id, sensor_callback in self.callback_map.items():
                        await client.start_notify(self.options.sensors[sensor_id].uuid, sensor_callback)

                    while (client.is_connected or self.signal_disconnect):
                        # sleep while the client is connected or until something requests to halt the communications
                        await asyncio.sleep(10)

                        # ping biosticker
                        await client.write_gatt_char(self.options.flags[BiostickerOptionsParser.PING_FLAG_ENTRY].uuid, bytearray([0x01]))

                if (self.signal_disconnect):
                    self.logger.info("Device disconnected properly.")
                else:
                    self.logger.info(
                        "Device disconnected unexpectedly, trying again...")

            except bleak.exc.BleakDeviceNotFoundError:
                self.logger.error("Device couldn't be found, trying again..")

            except bleak.exc.BleakDBusError:
                self.logger.exception("Caught unknown DBus error.")
                raise

            except:
                self.logger.exception("Caught unknown error.")
                raise

    def twos_comp(self, val, bits):
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val
