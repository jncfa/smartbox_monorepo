import json
import logging

from typing_extensions import final

@final 
class MQTTOptionsParser():
    """Configuration parser for the JSON config file."""

    # Constants used in the JSON file
    JSON_SECTION_ENTRY="MQTT_CONFIG"
    DEBUG_MODE_ENTRY="DEBUG"
    HOSTNAME_ENTRY="HOSTNAME"
    RECONNECT_INTERNAL_ENTRY="RECONNECT_INTERVAL"

    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            mqtt_config:dict = config[MQTTOptionsParser.JSON_SECTION_ENTRY]
            
            if (not isinstance(config.get(MQTTOptionsParser.DEBUG_MODE_ENTRY, False), bool)):
                raise TypeError(f'Expected type "{type(bool)}", got "{type(config[MQTTOptionsParser.DEBUG_MODE_ENTRY])}"' )
            
            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            # TODO: add type/value checking to each param
            self.debug_mode:bool = config.get(MQTTOptionsParser.DEBUG_MODE_ENTRY, False)
            self.hostname:str = mqtt_config[MQTTOptionsParser.HOSTNAME_ENTRY]
            self.reconnect_interval:str = mqtt_config[MQTTOptionsParser.RECONNECT_INTERNAL_ENTRY]

        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise  
        