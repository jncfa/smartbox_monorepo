import json
import logging

from typing_extensions import final

@final 
class OximeterConfigParser():
    """Configuration parser for the JSON config file."""

    # Constants used in the JSON file
    JSON_SECTION_ENTRY="OXIMETER_CONFIG"

    MAC_ADDR_ENTRY="MAC_ADDR"
    DEBUG_MODE_ENTRY="DEBUG"

    GATT_CHARACTERISTIC_SECTION_ENTRY="GATT_CHARACTERISTIC" # Section header
    GATT_CHARACTERISTIC_UUID_ENTRY="GATT_CHAR_UUID" # GATT UUID for setting up notifications / transmissions
    GATT_CHARACTERISTIC_NAME_ENTRY="GATT_CHAR_NAME" # Human readable name (to make it easier to interpret the config file)
    GATT_CHARACTERISTIC_PERIOD_ENTRY="GATT_CHAR_PERIOD_MS" # Expected time between measurements for the given sensor (in ms)

    # List of sensors used in the biosticker (this will be helpful for )
    SPO2_SENSOR_ENTRY = "OxiSPO2"

    BIOSTICKER_TYPE="TYPE"

    # one day we might have a better definition for this
    BIOSTICKER_TYPE_BLACK="BLACK"
    BIOSTICKER_TYPE_BLUE="BLUE"
    BIOSTICKER_SUPPORTED_TYPES = [
        BIOSTICKER_TYPE_BLACK,
        BIOSTICKER_TYPE_BLUE
    ]

    SENSOR_LIST = [
        SPO2_SENSOR_ENTRY
    ]


    #OXIMETER_SENSOR_LIST = [
    #    "OxiSPO2",
    #]

    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            biosticker_config:dict = config[OximeterConfigParser.JSON_SECTION_ENTRY]
            
            if (not isinstance(config.get(OximeterConfigParser.DEBUG_MODE_ENTRY, False), bool)):
                raise TypeError(f'Expected type "{str}", got "{type(config[OximeterConfigParser.DEBUG_MODE_ENTRY])}"' )
            
            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            self.debug_mode:bool = config.get(OximeterConfigParser.DEBUG_MODE_ENTRY, False)
            self.mac_address:str = biosticker_config[OximeterConfigParser.MAC_ADDR_ENTRY]
            self.sensors:dict = {}
            self.flags:dict = {}

            gatt_chars_config = biosticker_config[OximeterConfigParser.GATT_CHARACTERISTIC_SECTION_ENTRY]
            for sensor in OximeterConfigParser.SENSOR_LIST:
                sensor_config = gatt_chars_config[sensor]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'json' type, got {type(sensor_config)}")
                else:
                    # raise exceptions if type doesn't match expected type
                    if (not isinstance(sensor_config[OximeterConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                        raise TypeError(f'"{OximeterConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(sensor_config[OximeterConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')
                    if (not isinstance(sensor_config[OximeterConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{OximeterConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "float", got {type(sensor_config[OximeterConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(sensor_config[OximeterConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{OximeterConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "float", got {type(sensor_config[OximeterConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                
                    # don't blindly import other keys if configured
                    self.sensors[sensor] = {
                        entry: sensor_config[entry] 
                        for entry in [
                            OximeterConfigParser.GATT_CHARACTERISTIC_PERIOD_ENTRY,
                            OximeterConfigParser.GATT_CHARACTERISTIC_NAME_ENTRY,
                            OximeterConfigParser.GATT_CHARACTERISTIC_UUID_ENTRY
                        ]
                    }
                        
        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise  
        