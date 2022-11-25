import asyncio
from concurrent.futures import ProcessPoolExecutor
from .respiration_code import *

class RespirationProcessorWrapper:
    def __init__(self) -> None:
        self._inner_process_pool = ProcessPoolExecutor(max_workers=8)
        self._sensor1 = []
        self._sensor2 = []
        
    def is_ready(self) -> bool:
        return (len(self._sensor1) == 150) or (len(self._sensor2) == 150)

    async def compute_resp(self) -> float:
        # create a copy of the internal buffers so we don't have race conditions
        rpm = asyncio.get_running_loop().run_in_executor(self._inner_process_pool, computeResp, self._sensor1.copy(), self._sensor2.copy())
        
        # reset internal buffers before awaiting
        self._sensor1=[]
        self._sensor2=[]
        
        # return awaited value
        return await rpm
        
    def append_rr1(self, data, timestamp) -> None:
        self._sensor1.append(data)

    def append_rr2(self, data, timestamp) -> None:
        self._sensor2.append(data)
    