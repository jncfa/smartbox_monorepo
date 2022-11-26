from typing import NamedTuple, Any
from datetime import datetime


HEARTRATE_SENSOR_EVENT = "BioHR"
ECG_SENSOR_EVENT = "BioECG"
TEMPERATURE_SENSOR_EVENT = "BioTEMP"
BATTERY_SENSOR_EVENT = "BioBAT"
RR_SENSOR_EVENT = "BioRR"
RR1_SENSOR_EVENT = "BioRR1"
RR2_SENSOR_EVENT = "BioRR2"
IMU_SENSOR_EVENT = "BioIMU"
PR_SENSOR_EVENT = "OxiPR"
SPO2_SENSOR_EVENT = "OxiSPO2"

class QueueItem(NamedTuple):
    id: str
    timestamp: datetime
    data: Any
