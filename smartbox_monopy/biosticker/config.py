import json
import logging

from typing_extensions import final

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
    
    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            biosticker_config:dict = config[BiostickerConfigParser.JSON_SECTION_ENTRY]

            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            self.debug_mode:bool = config.get(BiostickerConfigParser.DEBUG_MODE_ENTRY, False)
            self.mac_address:str = biosticker_config[BiostickerConfigParser.MAC_ADDR_ENTRY]
            self.sensors:dict = {} # TODO: C
            self.flags:dict = {}

            gatt_chars_config = biosticker_config[BiostickerConfigParser.GATT_CHARACTERISTIC_SECTION_ENTRY]
            for sensor in BiostickerConfigParser.SENSOR_LIST:
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
                flag_config = gatt_chars_config[flag]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'json' type, got {type(sensor_config)}")
                else:
                    if (not isinstance(flag_config[BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "float", got {type(flag_config[BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(flag_config[BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "float", got {type(flag_config[BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                
                    if sensor == BiostickerConfigParser.PING_FLAG_ENTRY:
                        # raise exceptions if type doesn't match expected type
                        if (not isinstance(flag_config[BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                            raise TypeError(f'"{BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(flag_config[BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')

                        # don't blindly import other keys if configured
                        self.flags[flag] = {
                            entry: flag_config[entry] 
                            for entry in [
                                BiostickerConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY,
                                BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY,
                                BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY
                            ]
                        }
                    else: 
                        # don't blindly import other keys if configured
                        self.flags[flag] = {
                            entry: flag_config[entry] 
                            for entry in [
                                BiostickerConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY,
                                BiostickerConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY
                            ]
                        }
                        
        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise  
        