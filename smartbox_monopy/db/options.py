import json
import logging

from typing_extensions import final

@final 
class MongoDbOptionsParser():
    """Configuration parser for the JSON config file."""

    # Constants used in the JSON file
    JSON_SECTION_ENTRY="DB_CONFIG"
    HOSTNAME_ENTRY="HOSTNAME"
    DEBUG_MODE_ENTRY="DEBUG"

    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            db_config:dict = config[MongoDbOptionsParser.JSON_SECTION_ENTRY]
            
            if (not isinstance(config.get(MongoDbOptionsParser.DEBUG_MODE_ENTRY, False), bool)):
                raise TypeError(f'Expected type "{type(bool)}", got "{type(config[MongoDbOptionsParser.DEBUG_MODE_ENTRY])}"' )
            
            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            # TODO: add type/value checking to each param
            self.debug_mode:bool = config.get(MongoDbOptionsParser.DEBUG_MODE_ENTRY, False)
            self.hostname:str = db_config[MongoDbOptionsParser.HOSTNAME_ENTRY]
              
        except KeyError:
            if logger is not None: logger.exception("Failed to parse configuration file, file does not define all needed entries")
            raise
        
        except Exception:
            if logger is not None: logger.exception("Got an unknown error parsing the configuration file")
            raise  
        