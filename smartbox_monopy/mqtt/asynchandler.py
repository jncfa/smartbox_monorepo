

# the mqtt client handles the MQTT broker requests, and handles the data transformation into MQTT transmissions
#Version 1.0

import random
import time
from datetime import datetime, timedelta
import ssl, json, sys, time, threading
# from turtle import ycor
#import socket

from paho.mqtt import client as mqtt
import logging

import numpy as np

from smartbox_monopy.processing.queueitem import *

import os

first_connection=datetime.timestamp(datetime.now() )


class MQTTClientHandler():

    def __init__(self, config, db_handler, data_queue):
    #def __init__(self, mqttclient, reconnect):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.certificate_auth_file = certificate_auth_file
        self.cert_pem_file = cert_pem_file
        self.private_key_file = private_key_file
        self.verbose = verbose
        self.mongodb = mongodb

        # self.logger = logging.getLogger('mqttservice')
        with open('../smartbox_ble_acquisition/config.json') as f:
            self.config = json.load(f)

    def connect_mqtt(self):
        print("Connecting to MQTT Broker...")
        self.datainicio = datetime.now() 
        client = mqtt.Client(self.client_id)
        # client.enable_logger(logging.getLogger('pahomqtt'))

        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("lwt"),
            "payload": ''
            }

        client.will_set(topic=self.config.get("topicResponses").get("lwt").format(self.client_id), payload=json.dumps(message))

        client.on_connect = self.on_connect
        client.on_subscribe = self.on_subscribe
        client.on_disconnect = self.on_disconnect

        client.tls_set(self.certificate_auth_file, self.cert_pem_file,
                                self.private_key_file, tls_version=ssl.PROTOCOL_TLSv1_2)
        client.tls_insecure_set(False)


        client.connect(self.broker, self.port, 60)
        
        return client

    def on_connect(self,client, userdata, flags,rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)
           
            subscriptionList = []

            # Connected, now generate subscription list 
            for entry in self.config.get("topicSubscriptions"):
                topicName = self.config.get("topicSubscriptions").get(entry)
                # for request/response topics
                if isinstance(topicName, dict):
                    for subtopicName in topicName:
                        subscriptionList.append((topicName.get(subtopicName),2))
                else:
                    subscriptionList.append((topicName),2)

            client.subscribe(subscriptionList)

    def on_subscribe(self,client, userdata, flags, reasonCodes):
            # sync messages
            client.message_callback_add(self.config.get("topicSubscriptions").get("sync").get("request"), self.on_sync_request_recieved)
            # status messages
            client.message_callback_add(self.config.get("topicSubscriptions").get("status").get("request"), self.on_status_request_recieved) 

            client.message_callback_add(self.config.get("topicSubscriptions").get("pair").get("response"), self.on_pair_response_recieved)     
            
    def on_disconnect(self,client, userdata, reasonCodes):
        print("Discconected.")
   
    def is_valid_message(self, message):

        # check if message is a JSON object
        if (not isinstance(message, dict)):
            return False

        
        # check payload depending on message_type
        messageType = message.get("message_type")
        payload = message.get("payload")
         # check sync request payload
        if (messageType == self.config.get("messageTypes").get("sync").get("request")):
            payloadKeys = set(payload.keys())
            if (payloadKeys != {"last_message_timestamp"}):
                return False
            
        
         # check sync request payload
        elif (messageType == self.config.get("messageTypes").get("status").get("request")):
            if (not isinstance(payload, str)):
                return True

        else: # unknown message type 
            return False

        # message passed every check
        return True

    # Callback for received message in the status topics
    def on_status_request_recieved(self, client, userdata, msg):
        # import message payload
        topic=self.config.get("topicResponses").get("status").get("response").format(self.client_id)
        message = json.loads(msg.payload)
        if (self.is_valid_message(message)):

            message_s = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("status").get("response"),
            "payload": {"connection_start_timestamp":  first_connection} 
        }
            result = client.publish(topic, json.dumps(message_s))

            status = result[0]

            if self.verbose:
                if status == 0:
                    print(f"Send `{message_s}` to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic {topic}")
        else:
            print("Mensagem STATUS inválida.")       

    # Callback for received message in the sync topics
    def on_sync_request_recieved(self, client, userdata, msg):

        thread_mqtt = threading.Thread(target=self.syncing,args=(client, userdata, msg))
        thread_mqtt.start()

    # Function to handle syncing mechanism
    def syncing(self, client, userdata, msg):
        topic=self.config.get("topicResponses").get("sync").get("response").format(self.client_id)
    
        batch_size=99438 # 15 mins de dados
        batch_size_imu=18001 #15 mins de dados
        timestampinicio=datetime.fromtimestamp(message.get("timestamp")) 
        timestampfim=self.datainicio 

        message = json.loads(msg.payload)
        message_list=[]
        if (self.is_valid_message(message)):
            for item in self.mongodb.sensors_collection.find({ "timestamp": { "$gt": timestampinicio, "$lt":  timestampfim}}):   
                if "ECG" in item.get("name"):
                    message_list.append({  
                        "timestamp": datetime.timestamp(item.get("timestamp")), 
                        "message_type": self.config.get("messageTypes").get("ecg"),
                        "payload": {"ecg" : item.get("value")} 
                        })
                if "Temperature" in item.get("name"):
                    message_list.append({  
                        "timestamp": datetime.timestamp(item.get("timestamp")), 
                        "message_type": self.config.get("messageTypes").get("temperature"),
                        "payload": {"temperature" : item.get("value"), "is_celsius" : True} 
                        })
                if "Heart Rate" in item.get("name"):
                    message_list.append({  
                        "timestamp": datetime.timestamp(item.get("timestamp")), 
                        "message_type": self.config.get("messageTypes").get("heartrate"),
                        "payload": {"bpm" : item.get("value")} 
                        })
                if "Respiratory Rate" in item.get("name"):
                    message_list.append({  
                        "timestamp": datetime.timestamp(item.get("timestamp")), 
                        "message_type": self.config.get("messageTypes").get("respiration"),
                        "payload": {"respiration" : item.get("value")} 
                        })
                if "Oxygen Saturation" in item.get("name"):
                    message_list.append({  
                        "timestamp": datetime.timestamp(item.get("timestamp")), 
                        "message_type": self.config.get("messageTypes").get("pulseoximetry"),
                        "payload": {"spo2" : item.get("value")} 
                        })
                if len(message_list) == batch_size:
                    message_s = {
                        "client_id": self.client_id, 
                        "timestamp": datetime.timestamp(datetime.now() ), 
                        "message_type": self.config.get("messageTypes").get("sync").get("response"),
                        "payload": {
                            "message_list":  message_list
                        }
                    }
                    result = client.publish(topic, json.dumps(message_s))
                    message_s.clear()
                    message_list.clear()

                    status = result[0]

                    if self.verbose:
                        if status == 0:
                            print(f"Send `{message_s}` to topic `{topic}`")
                        else:
                            print(f"Failed to send message to topic {topic}")

            if len(message_list) != 0:
                message_s = {
                            "client_id": self.client_id, 
                            "timestamp": datetime.timestamp(datetime.now() ), 
                            "message_type": self.config.get("messageTypes").get("sync").get("response"),
                            "payload": {
                                "message_list":  message_list}
                }
                result = client.publish(topic, json.dumps(message_s))
                status = result[0]

                if self.verbose:
                    if status == 0:
                        print(f"Send `{message_s}` to topic `{topic}`")
                    else:
                        print(f"Failed to send message to topic {topic}")

                message_s.clear()
                message_list.clear()

            for item in self.mongodb.sensors_collection_imu.find({ "timestamp": { "$gt": timestampinicio, "$lt":  timestampfim}}):
                if "IMU" in item.get("name"):
                   message_list.append({  
                       "timestamp": datetime.timestamp(item.get("timestamp")), 
                       "message_type": self.config.get("messageTypes").get("imu"),
                       "payload": {"imu": { "linear_acceleration": {"x": item.get("value_acc_x"), "y": item.get("value_acc_y"), "z": item.get("value_acc_z")}, "angular_velocity": {"x": item.get("value_gyr_x"), "y": item.get("value_gyr_y"), "z": item.get("value_gyr_z")}}, "pose_description" : "SITTING"}
                       })
                if len(message_list) == batch_size_imu:
                    message_s = {
                        "client_id": self.client_id, 
                        "timestamp": datetime.timestamp(datetime.now() ), 
                        "message_type": self.config.get("messageTypes").get("sync").get("response"),
                        "payload": {
                            "message_list":  message_list
                        }
                    }
                    message_s.clear()
                    message_list.clear()

                    status = result[0]

                    if self.verbose:
                        if status == 0:
                            print(f"Send `{message_s}` to topic `{topic}`")
                        else:
                            print(f"Failed to send message to topic {topic}")

            if len(message_list) != 0:
                message_s = {
                            "client_id": self.client_id, 
                            "timestamp": datetime.timestamp(datetime.now() ), 
                            "message_type": self.config.get("messageTypes").get("sync").get("response"),
                            "payload": {
                                "message_list":  message_list}
                }
                status = result[0]
                
                message_s.clear()
                message_list.clear()
                if self.verbose:
                    if status == 0:
                        print(f"Send `{message_s}` to topic `{topic}`")
                    else:
                        print(f"Failed to send message to topic {topic}")
            
            message_end = {
                            "client_id": self.client_id, 
                            "timestamp": datetime.timestamp(datetime.now() ), 
                            "message_type": self.config.get("messageTypes").get("sync").get("response_end"),
                            "payload": ''
            } 
            result = client.publish(topic, json.dumps(message_end))
            status = result[0]

            
            if self.verbose:
                if status == 0:
                    print(f"Send `{message_s}` to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic {topic}")

    def on_pair_response_recieved(self, client, userdata, msg):
        pass

    # function to publish pair request
    def publish_pair_request(self, client,  mac_adress):
        topic=self.config.get("topicResponses").get("pair").get("request").format(self.client_id)

        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("pair").get("request"),
            "payload": { "mac_addr": mac_adress } 
        }

        result = client.publish(topic, json.dumps(message))
        status = result[0]

        if self.verbose:
                if status == 0:
                    print(f"Send `{message}` to topic `{topic}`")
                else:
                    print(f"Failed to send message to topic {topic}")



    def publish_heart_rate(self, client,  value):
        topic = self.config["characteristics"]["Heart Rate"]["topic"].format(self.client_id)    
        
        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("heartrate"),
            "payload": {"bpm" : value} 
        }

        result = client.publish(topic, json.dumps(message))
        
        status = result[0]

        if self.verbose:
            if status == 0:
                print(f"Send `{message}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")

    def publish_temperature(self, client, value):
        topic = self.config["characteristics"]["Temperature"]["topic"].format(self.client_id)    
        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("temperature"),
            "payload": {"temperature" : value, "is_celsius" : True} 
        }

        result = client.publish(topic, json.dumps(message))
        
        status = result[0]

        if self.verbose:
            if status == 0:
                print(f"Send `{message}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")


    def publish_respiratory_rate(self, client, value):
        topic = self.config["characteristics"]["RR"]["topic"].format(self.client_id)        
        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("respiration"),
            "payload": {"respiration" : value} 
        }

        result = client.publish(topic, json.dumps(message))
        
        status = result[0]
        timestamp_mqtt = datetime.now() 
        if self.verbose:
            if status == 0:
                print(f"Send `{message}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")

    def publish_ecg(self, client, value,timestamp):
        topic = self.config["characteristics"]["ECG"]["topic"].format(self.client_id)    
        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(timestamp), 
            "message_type": self.config.get("messageTypes").get("ecg"),
            "payload": {"ecg" : value} 
        }

        result = client.publish(topic, json.dumps(message))
        
        status = result[0]
        if self.verbose:
            if status == 0:
                print(f"Send `{message}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")


    def publish_imu(self, client, x_linear_acceleration, y_linear_acceleration, z_linear_acceleration, x_angular_velocity, y_angular_velocity, z_angular_velocity, pose_description, timestamp):
        topic = self.config["characteristics"]["IMU"]["topic"].format(self.client_id)
        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(timestamp), 
            "message_type": self.config.get("messageTypes").get("imu"),
            "payload": {"imu": { "linear_acceleration": {"x": x_linear_acceleration, "y": y_linear_acceleration, "z": z_linear_acceleration}, "angular_velocity": {"x": x_angular_velocity, "y": y_angular_velocity, "z": z_angular_velocity}}, "pose_description" : pose_description}
            }
        result = client.publish(topic, json.dumps(message))
        
        status = result[0]
        if self.verbose:
            if status == 0:
                print(f"Send `{message}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")

    def publish_pulse_oximetry(self, client,value):
        topic = self.config["characteristics"]["Oximetry"]["topic"].format(self.client_id)
        message = {
            "client_id": self.client_id, 
            "timestamp": datetime.timestamp(datetime.now() ), 
            "message_type": self.config.get("messageTypes").get("pulseoximetry"),
            "payload": {"spo2" : value} 
        }

        result = client.publish(topic, json.dumps(message))
        
        status = result[0]
        if self.verbose:
            if status == 0:
                print(f"Send `{message}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")

