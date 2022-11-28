import json
import logging

from typing import NamedTuple, Dict, Union
from typing_extensions import final
import uuid

import asyncio_mqtt as aiomqtt

from smartbox_monopy.processing.queueitem import *


@final 
class MQTTOptionsParser():
    """Configuration parser for the JSON config file."""

    DEBUG_MODE_ENTRY='DEBUG'
    CLIENT_UUID = 'CLIENT_UUID'
    
    # Constants used in the JSON file
    JSON_SECTION_ENTRY='MQTT_CONFIG'
    
    HOST_ENTRY='HOST'
    PORT_ENTRY='PORT'
    KEEP_ALIVE_ENTRY='KEEP_ALIVE'
    RECONNECT_INTERNAL_ENTRY='RECONNECT_INTERVAL'
    QOS_ENTRY='QOS'
    DISABLE_MQTT_ENTRY = 'DISABLE_MQTT'

    TLS_CONFIG_SECTION_ENTRY = 'TLS_CONFIG'
    CA_CERT_FILE_ENTRY = 'CA_CERT_FILE'
    CLIENT_CERT_FILE_ENTRY = 'CLIENT_CERT_FILE'
    CLIENT_KEY_FILE_ENTRY= 'CLIENT_KEY_FILE'
    
    TLS_CONFIG_ENTRIES = [
        CA_CERT_FILE_ENTRY,
        CLIENT_CERT_FILE_ENTRY,
        CLIENT_KEY_FILE_ENTRY
    ]

    def __init__(self, config: dict, logger: logging.Logger) -> None:
        """Parse the supplied config file. The class checks if the config defines all required keys to continue execution. """
        try:
            mqtt_config:dict = config[MQTTOptionsParser.JSON_SECTION_ENTRY]

            self.disable_mqtt: bool = mqtt_config.get(MQTTOptionsParser.DISABLE_MQTT_ENTRY, False) 

            if self.disable_mqtt:
                return # don't process the remainder of the config if we have disabled MQTT
            
            if (not isinstance(config.get(MQTTOptionsParser.DEBUG_MODE_ENTRY, False), bool)):
                raise TypeError(f'Expected type "{type(bool)}", got "{type(config[MQTTOptionsParser.DEBUG_MODE_ENTRY])}"' )
        

            # don't fail if debug is not defined, assume it's always release mode in case it doesn't exist
            # TODO: add type/value checking to each param
            self.debug_mode: bool = config.get(MQTTOptionsParser.DEBUG_MODE_ENTRY, False)
            self.client_uuid = uuid.UUID(config[MQTTOptionsParser.CLIENT_UUID])

            self.host: str = mqtt_config[MQTTOptionsParser.HOST_ENTRY]
            self.port: int = mqtt_config[MQTTOptionsParser.PORT_ENTRY]

            self.keep_alive: int = mqtt_config[MQTTOptionsParser.KEEP_ALIVE_ENTRY]
            self.qos: int = mqtt_config[MQTTOptionsParser.QOS_ENTRY]
            self.reconnect_interval: float = mqtt_config[MQTTOptionsParser.RECONNECT_INTERNAL_ENTRY]
                        
            tls_raw_config = mqtt_config.get(MQTTOptionsParser.TLS_CONFIG_SECTION_ENTRY, None)

            self.tls_config = None
            if (tls_raw_config is not None):
                if (not isinstance(tls_raw_config, dict)):
                    raise TypeError(f"Expected 'dict' type, got {type(tls_raw_config)}")
                else:
                    # raise exceptions if type doesn't match expected type
                    if (not isinstance(tls_raw_config[MQTTOptionsParser.CA_CERT_FILE_ENTRY], str)):
                        raise TypeError(f'"{MQTTOptionsParser.CA_CERT_FILE_ENTRY}" should be "float", got {type(tls_raw_config[MQTTOptionsParser.CA_CERT_FILE_ENTRY])}')
                    if (not isinstance(tls_raw_config[MQTTOptionsParser.CLIENT_CERT_FILE_ENTRY], str)):
                        raise TypeError(f'"{MQTTOptionsParser.CLIENT_CERT_FILE_ENTRY}" should be "str", got {type(tls_raw_config[MQTTOptionsParser.CLIENT_CERT_FILE_ENTRY])}')
                    if (not isinstance(tls_raw_config[MQTTOptionsParser.CLIENT_KEY_FILE_ENTRY], str)):
                        raise TypeError(f'"{MQTTOptionsParser.CLIENT_KEY_FILE_ENTRY}" should be "str", got {type(tls_raw_config[MQTTOptionsParser.CLIENT_KEY_FILE_ENTRY])}')
                    
                self.tls_config = aiomqtt.TLSParameters(
                    ca_certs=tls_raw_config[MQTTOptionsParser.CA_CERT_FILE_ENTRY],
                    certfile=tls_raw_config[MQTTOptionsParser.CLIENT_CERT_FILE_ENTRY],
                    keyfile=tls_raw_config[MQTTOptionsParser.CLIENT_KEY_FILE_ENTRY],
                )
            
            # map that indicates the topic used for the given event
            self.event_topic_map = {
                # sensor publish events
                QueueEvent.HEARTRATE_SENSOR_EVENT: f'smartbox/{str(self.client_uuid)}/heartrate',
                QueueEvent.ECG_SENSOR_EVENT: f'smartbox/{str(self.client_uuid)}/ecg',
                QueueEvent.TEMPERATURE_SENSOR_EVENT: f'smartbox/{str(self.client_uuid)}/temperature',
                QueueEvent.RR_SENSOR_EVENT: f'smartbox/{str(self.client_uuid)}/respiration',
                QueueEvent.IMU_SENSOR_EVENT: f'smartbox/{str(self.client_uuid)}/imu',
                QueueEvent.SPO2_SENSOR_EVENT: f'smartbox/{str(self.client_uuid)}/pulseoximetry',

                # mqtt specific events
                QueueEvent.MQTT_SYNC_REQ_EVENT: f'smartbox/{str(self.client_uuid)}/sync',
                QueueEvent.MQTT_SYNC_REP_EVENT: f'smartbox/{str(self.client_uuid)}/sync/response',
                QueueEvent.MQTT_SYNC_FINAL_REP_EVENT: f'smartbox/{str(self.client_uuid)}/sync/response',
                QueueEvent.MQTT_STATUS_REQ_EVENT:  'status', 
                QueueEvent.MQTT_STATUS_REP_EVENT: f'status/{str(self.client_uuid)}', 
                QueueEvent.MQTT_WILL_EVENT: f'smartbox/{str(self.client_uuid)}/lwt',
                QueueEvent.MQTT_PAIR_REQ_EVENT: f'smartbox/{str(self.client_uuid)}/pair',
                QueueEvent.MQTT_PAIR_REP_EVENT: f'smartbox/{str(self.client_uuid)}/pair/response'
            }
            
            # these are technically constants, but it won't really affect performance

            self.event_message_type_map = {
                # sensor publish events
                QueueEvent.HEARTRATE_SENSOR_EVENT: 'MEASUREMENT_HEARTRATE',
                QueueEvent.ECG_SENSOR_EVENT: 'MEASUREMENT_ECG',
                QueueEvent.TEMPERATURE_SENSOR_EVENT: 'MEASUREMENT_TEMPERATURE',
                QueueEvent.RR_SENSOR_EVENT: 'MEASUREMENT_RESPIRATION',
                QueueEvent.IMU_SENSOR_EVENT: 'MEASUREMENT_IMU',
                QueueEvent.SPO2_SENSOR_EVENT: 'MEASUREMENT_PULSEOXIMETRY',
                
                # mqtt specific events
                QueueEvent.MQTT_SYNC_REQ_EVENT: 'SYNC_REQ', 
                QueueEvent.MQTT_SYNC_REP_EVENT: 'SYNC_REP',
                QueueEvent.MQTT_SYNC_FINAL_REP_EVENT: 'SYNC_REP_END',
                QueueEvent.MQTT_STATUS_REQ_EVENT:  'STATUS_REQ', 
                QueueEvent.MQTT_STATUS_REP_EVENT: 'STATUS_REP', 
                QueueEvent.MQTT_WILL_EVENT: 'WILL_BRD',
                QueueEvent.MQTT_PAIR_REQ_EVENT: 'PAIR_REQ',
                QueueEvent.MQTT_PAIR_REP_EVENT: 'PAIR_REP'
            }

        except KeyError:
            if logger is not None: logger.exception('Failed to parse configuration file, file does not define all needed entries')
            raise
        except ValueError:
            if logger is not None: logger.exception('Failed to parse configuration file, file does not define all needed entries')
            raise
        except Exception:
            if logger is not None: logger.exception('Got an unknown error parsing the configuration file')
            raise  
        