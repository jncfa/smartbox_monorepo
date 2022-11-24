import json
import logging

from typing import NamedTuple, Any
from typing_extensions import final

class GATTCharacteristic(NamedTuple):
    uuid: str
    name: str
    period: float = None

    def todict(self) -> dict:
        return {
            OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY: self.uuid,
            OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY: self.name,
            OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY: self.period
        }


@final 
class OximeterOptionsParser():
    """Configuration parser for the JSON config file."""

    # Constants used in the JSON file
    JSON_SECTION_ENTRY="OXIMETER_CONFIG"
    ADAPTER_ID_ENTRY="ADAPTER_ID"
    MAC_ADDR_ENTRY="MAC_ADDR"
    DEBUG_MODE_ENTRY="DEBUG"

    GATT_CHARACTERISTIC_SECTION_ENTRY="GATT_CHARACTERISTIC" # Section header
    GATT_CHARACTERISTIC_UUID_ENTRY="GATT_CHAR_UUID" # GATT UUID for setting up notifications / transmissions
    GATT_CHARACTERISTIC_NAME_ENTRY="GATT_CHAR_NAME" # Human readable name (to make it easier to interpret the config file)
    GATT_CHARACTERISTIC_PERIOD_ENTRY="GATT_CHAR_PERIOD_MS" # Expected time between measurements for the given sensor (in ms)

    # List of sensors used in the biosticker 
    PR_SENSOR_ENTRY = "OxiPR"
    SPO2_SENSOR_ENTRY = "OxiSPO2"
    PRSPO2_SENSOR_ENTRY = "OxiPRSPO2"
    INIT_FLAG_ENTRY = "OxiInit"

    BIOSTICKER_TYPE="TYPE"

    # one day we might have a better definition for this
    BIOSTICKER_TYPE_BLACK="BLACK"
    BIOSTICKER_TYPE_BLUE="BLUE"

    BIOSTICKER_SUPPORTED_TYPES = [
        BIOSTICKER_TYPE_BLACK,
        BIOSTICKER_TYPE_BLUE
    ]

    SENSOR_LIST = [
        PRSPO2_SENSOR_ENTRY
    ]

    FLAG_LIST = [
        INIT_FLAG_ENTRY
    ]

    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            biosticker_config:dict = config[OximeterOptionsParser.JSON_SECTION_ENTRY]
            
            if (not isinstance(config.get(OximeterOptionsParser.DEBUG_MODE_ENTRY, False), bool)):
                raise TypeError(f'Expected type "{type(bool)}", got "{type(config[OximeterOptionsParser.DEBUG_MODE_ENTRY])}"' )
            
            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            # TODO: add type/value checking to each param
            self.debug_mode: bool = config.get(OximeterOptionsParser.DEBUG_MODE_ENTRY, False)
            self.mac_address: str = biosticker_config[OximeterOptionsParser.MAC_ADDR_ENTRY]
            self.adapter_id: str = biosticker_config[OximeterOptionsParser.ADAPTER_ID_ENTRY]
            self.oximeter_type: str = biosticker_config[OximeterOptionsParser.BIOSTICKER_TYPE]
            self.sensors: dict = {}
            self.flags: dict = {}

            gatt_chars_config = biosticker_config[OximeterOptionsParser.GATT_CHARACTERISTIC_SECTION_ENTRY]
           
            for sensor in OximeterOptionsParser.SENSOR_LIST:
                sensor_config = gatt_chars_config[sensor]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'dict' type, got {type(sensor_config)}")
                else:
                    # raise exceptions if type doesn't match expected type
                    if (not isinstance(sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "str", got {type(sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "str", got {type(sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                    if (not isinstance(sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                            raise TypeError(f'"{OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')
                        
                    # don't blindly import other keys if configured
                    self.sensors[sensor] = GATTCharacteristic(
                        sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY],
                        sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY],
                        sensor_config[OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY]
                    )
                    
            
            for flag in OximeterOptionsParser.FLAG_LIST:
                flag_config = gatt_chars_config[flag]

                if (not isinstance(sensor_config, dict)):
                    raise TypeError(f"Expected 'dict' type, got {type(sensor_config)}")
                else:
                    if (not isinstance(flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY], str)):
                        raise TypeError(f'"{OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY}" should be "str", got {type(flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY])}')
                    if (not isinstance(flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY], str)):
                        raise TypeError(f'"{OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY}" should be "str", got {type(flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY])}')
                
                    if not flag == OximeterOptionsParser.INIT_FLAG_ENTRY:
                        # raise exceptions if type doesn't match expected type
                        if (not isinstance(flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY], float)):
                            raise TypeError(f'"{OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY}" should be "float", got {type(flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY])}')

                        self.flags[flag] = GATTCharacteristic(
                            flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY],
                            flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY],
                            flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_PERIOD_ENTRY]
                        )
                    else: 
                        # don't blindly import other keys if configured
                        self.flags[flag] = GATTCharacteristic(
                            flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_UUID_ENTRY],
                            flag_config[OximeterOptionsParser.GATT_CHARACTERISTIC_NAME_ENTRY]
                        )
                        
        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise  
        