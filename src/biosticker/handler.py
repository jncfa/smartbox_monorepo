import asyncio
import bleak
import json
import logging
import logging.config
import time
from typing_extensions import final

@final
class BiostickerBLEHandler():
    """
    
    """
    def __init__(self, config) -> None:
        self.last_timestamps = {}
        self.logger = logging.getLogger("biosticker")
        self.config = config

    def handle_data_imu(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'IMU: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_heart_rate(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'HR: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_temperature(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Temp: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_battery(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'BAT: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_respiratory_rate(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'RR1: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_respiratory_rate_2(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'RR2: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_ecg(self, char: bleak.BleakGATTCharacteristic, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'ECG: took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    # async def connect_to_biosticker(self, config: dict):
    #     #try:
    #     async with bleak.BleakClient(config["biosticker_simulated_mac_address"], adapter='hci0', disconnected_callback=(lambda client : logger.info("Device disconnected"))) as client:
    #         self.logger.info("Device connected")
        
    #         biostickerLogger = BiostickerLogger(logger, config)
    #         # select emulation mode
    #         await client.write_gatt_char(config["characteristics"]["Select Flag"]["uuid"], bytearray([0x0A]))
            
    #         # configure notification on every characteristic
    #         await client.start_notify(config["characteristics"]["IMU"]["uuid"], biostickerLogger.handle_data_imu)
    #         await client.start_notify(config["characteristics"]["Heart Rate"]["uuid"], biostickerLogger.handle_data_heart_rate)
    #         await client.start_notify(config["characteristics"]["Temperature"]["uuid"], biostickerLogger.handle_data_temperature)
    #         await client.start_notify(config["characteristics"]["Battery"]["uuid"], biostickerLogger.handle_data_battery)
    #         await client.start_notify(config["characteristics"]["RR_1"]["uuid"], biostickerLogger.handle_data_respiratory_rate)
    #         await client.start_notify(config["characteristics"]["RR_2"]["uuid"], biostickerLogger.handle_data_respiratory_rate_2)
    #         await client.start_notify(config["characteristics"]["ECG"]["uuid"], biostickerLogger.handle_data_ecg)

    #         while (client.is_connected):
    #             await asyncio.sleep(10) # ping biosticker every ~10 seconds on the "ping flag" characteristic (the watchdog timer is 30s)
    #             await client.write_gatt_char(config["characteristics"]["Ping Flag"]["uuid"], bytearray([0x01]))


@final 
class BiostickerConfigParser():
    """Configuration parser for the JSON config file."""

    # Constants used in the JSON file
    JSON_SECTION_ENTRY="BIOSTICKER_CONFIG"
    MAC_ADDR_ENTRY="MAC_ADDR"
    DEBUG_MODE_ENTRY="DEBUG"

    GATT_CHARACTERISTIC_SECTION_ENTRY="GATT_CHARACTERISTIC" # Section header
    GATT_CHARACTERISTIC_UUID_ENTRY="GATT_CHAR_UUID" # GATT UUID for setting up notifications / transmissions
    GATT_CHARACTERISTIC_NAME_ENTRY="GATT_CHAR_NAME" # Human readable name (to make it easier to interpret the config file)
    GATT_CHARACTERISTIC_PERIOD_ENTRY="GATT_CHAR_PERIOD_MS" # Expected time between measurements for the given sensor (in ms)

    
    # List of sensors used in the biosticker (this will be helpful for )
    HEARTRATE_SENSOR_ENTRY = "BioHR"
    TEMPERATURE_SENSOR_ENTRY = "BioTEMP"
    BATTERY_SENSOR_ENTRY = "BioBAT"
    RR1_SENSOR_ENTRY = "BioRR1"
    RR2_SENSOR_ENTRY = "BioRR2"
    IMU_SENSOR_ENTRY = "BioIMU"

    # Special flags for our BLE protocol 
    PING_FLAG_ENTRY = "BioPING"
    SELECT_FLAG_ENTRY = "BioSELECT"
    
    SENSOR_LIST = [
        HEARTRATE_SENSOR_ENTRY,
        TEMPERATURE_SENSOR_ENTRY,
        BATTERY_SENSOR_ENTRY,
        RR1_SENSOR_ENTRY,
        RR2_SENSOR_ENTRY,
        IMU_SENSOR_ENTRY
    ]
    FLAGS_LIST = [
        PING_FLAG_ENTRY,
        SELECT_FLAG_ENTRY
    ]

    #OXIMETER_SENSOR_LIST = [
    #    "OxiSPO2",
    #]

    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            biosticker_config:dict = config[BiostickerConfigParser.JSON_SECTION_ENTRY]

            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            self.debug_mode:bool = config.get(BiostickerConfigParser.DEBUG_MODE_ENTRY, False)
            self.mac_address:str = biosticker_config[BiostickerConfigParser.MAC_ADDR_ENTRY]
            self.sensors:dict = []
            self.flags:dict = []

            gatt_chars_config = biosticker_config[BiostickerConfigParser.GATT_CHARACTERISTIC_SECTION_ENTRY]
            for sensor in BiostickerConfigParser.SENSOR_LIST:
                if logger is not None: logger.debug(f"Parsing {sensor=}")
                
                sensor_config = gatt_chars_config[sensor]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'json' type, got {type(sensor_config)}")
                else:
                    # raise exceptions if type doesn't match expected type
                    if (not isinstance(sensor_config[BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                        raise TypeError(f'"{BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(sensor_config[BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')
                    if (not isinstance(sensor_config[BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "float", got {type(sensor_config[BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(sensor_config[BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "float", got {type(sensor_config[BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                
                    # don't blindly import other keys if configured
                    self.sensors[sensor] = {
                        entry: sensor_config[entry]
                        for entry in [
                            BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY,
                            BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY,
                            BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY
                        ]
                    }
            
            for flag in BiostickerConfigParser.FLAGS_LIST:
                flag_config = biosticker_config[flag]

                if (isinstance(sensor_config, dict)):
                    pass
                else:
                    raise TypeError(f"Expected 'json' type, got {type(sensor_config)}")
            
        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise

        print(self.debug_mode)