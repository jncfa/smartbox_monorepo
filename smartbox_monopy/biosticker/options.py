import json
import logging

from typing import final, NamedTuple
from enum import Enum

# TODO: Rewrite code to use enums as shown below
#GATTJsonEntries = Enum('JsonGATTEntries', ['GATT_CHAR_UUID', 'GATT_CHAR_NAME', 'GATT_CHAR_PERIOD_MS'])
#JsonSensorEntries = Enum('JsonSensorEntries', ['GATT_CHAR_UUID', 'GATT_CHAR_NAME', 'GATT_CHAR_PERIOD_MS'])

class GATTCharacteristic(NamedTuple):
    uuid: str
    name: str
    period: float = None

    def todict(self) -> dict:
        return {
            BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY: self.uuid,
            BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY: self.name,
            BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY: self.period
        }

@final 
class BiostickerOptionsParser():
    """Configuration parser for the JSON config file."""

    # Constants used in the JSON file
    JSON_SECTION_ENTRY="BIOSTICKER_CONFIG" # json entry used to identify the config section
    ADAPTER_ID_ENTRY="ADAPTER_ID"
    MAC_ADDR_ENTRY="MAC_ADDR" # MAC Address of the biosticker
    DEBUG_MODE_ENTRY="DEBUG"
    SIM_BIOSTICKER_ENTRY = "SIM_BIOSTICKER"

    CONNECTION_RETRIES_ENTRY="CONNECTION_RETRIES_ENTRY" # number of connection tries (0 = inf)
    
    GATT_CHARACTERISTIC_SECTION_ENTRY="GATT_CHARACTERISTIC" # Section header
    GATT_CHARACTERISTIC_UUID_ENTRY="GATT_CHAR_UUID" # GATT UUID for setting up notifications / transmissions
    GATT_CHARACTERISTIC_NAME_ENTRY="GATT_CHAR_NAME" # Human readable name (to make it easier to interpret the config file)
    GATT_CHARACTERISTIC_PERIOD_ENTRY="GATT_CHAR_PERIOD_MS" # Expected time between measurements for the given sensor (in ms)
    
    # List of sensors used in the biosticker
    HEARTRATE_SENSOR_ENTRY = "BioHR"
    ECG_SENSOR_ENTRY = "BioECG"
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
        ECG_SENSOR_ENTRY,
        TEMPERATURE_SENSOR_ENTRY,
        BATTERY_SENSOR_ENTRY,
        RR1_SENSOR_ENTRY,
        RR2_SENSOR_ENTRY,
        IMU_SENSOR_ENTRY
    ]

    FLAG_LIST = [
        PING_FLAG_ENTRY,
        SELECT_FLAG_ENTRY
    ]
    
    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            biosticker_config:dict = config[BiostickerOptionsParser.JSON_SECTION_ENTRY]

            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
             # TODO: add type/value checking to each param
            self.debug_mode:bool = config.get(BiostickerOptionsParser.DEBUG_MODE_ENTRY, False)
            self.mac_address:str = biosticker_config[BiostickerOptionsParser.MAC_ADDR_ENTRY]
            self.adapter_id:str = biosticker_config[BiostickerOptionsParser.ADAPTER_ID_ENTRY]
            self.sensors:dict = {} # TODO: Turn this into an actual object later down the road
            self.flags:dict = {}
            self.is_sim_biosticker = biosticker_config.get(BiostickerOptionsParser.SIM_BIOSTICKER_ENTRY, False)
            gatt_chars_config = biosticker_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_SECTION_ENTRY]
            for sensor in BiostickerOptionsParser.SENSOR_LIST:
                sensor_config = gatt_chars_config[sensor]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'dict' type, got {type(sensor_config)}")
                else:
                    # raise exceptions if type doesn't match expected type
                    if (not isinstance(sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                        raise TypeError(f'"{BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')
                    if (not isinstance(sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "str", got {type(sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "str", got {type(sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                
                    # don't blindly import other keys if configured

                    self.sensors[sensor] = GATTCharacteristic(
                        sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY],
                        sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY],
                        sensor_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY]
                    )
            
            for flag in BiostickerOptionsParser.FLAG_LIST:
                flag_config = gatt_chars_config[flag]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'dict' type, got {type(sensor_config)}")
                else:
                    if (not isinstance(flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "float", got {type(flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "float", got {type(flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                
                    if flag == BiostickerOptionsParser.PING_FLAG_ENTRY:
                        # raise exceptions if type doesn't match expected type
                        if (not isinstance(flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                            raise TypeError(f'"{BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')

                        self.flags[flag] = GATTCharacteristic(
                            flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY],
                            flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY],
                            flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY]
                        )
                    else: 
                        # don't blindly import other keys if configured
                        self.flags[flag] = GATTCharacteristic(
                            flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY],
                            flag_config[BiostickerOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY]
                        )
                        
        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise  
        