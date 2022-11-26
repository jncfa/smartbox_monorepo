import asyncio
from concurrent.futures import ProcessPoolExecutor
from .respiration_code import *

class RespirationProcessorWrapper:
    INNER_BUFFER_SIZE = 150

    def __init__(self) -> None:
        self._inner_process_pool = ProcessPoolExecutor(max_workers=8)
        self._sensor1 = []
        self._sensor2 = []
        
    def is_ready(self) -> bool:
        return (len(self._sensor1) >= RespirationProcessorWrapper.INNER_BUFFER_SIZE) and (len(self._sensor2) >= RespirationProcessorWrapper.INNER_BUFFER_SIZE)

    async def compute_resp(self) -> float:
        if self.is_ready():
            # create a copy of the internal buffers so we don't have race conditions
            rpm = asyncio.get_running_loop().run_in_executor(self._inner_process_pool, computeResp, self._sensor1.copy()[:RespirationProcessorWrapper.INNER_BUFFER_SIZE], self._sensor2.copy()[:RespirationProcessorWrapper.INNER_BUFFER_SIZE])
            
            # reset internal buffers before awaiting (we keep whatever samples that weren't consumed)
            self._sensor1 = self._sensor1[RespirationProcessorWrapper.INNER_BUFFER_SIZE:]
            self._sensor2 = self._sensor2[RespirationProcessorWrapper.INNER_BUFFER_SIZE:]
            
            # return awaited value
            return await rpm
        else:
            raise RuntimeWarning("The wrapper didn't have enough information to process the respiration data, please use RespirationProcessWrapper.is_ready() to ensure you can use RespirationProcessWrapper.compute_resp().")
        
    def append_rr1(self, data, timestamp) -> None:
        self._sensor1.append(data)

    def append_rr2(self, data, timestamp) -> None:
        self._sensor2.append(data)
    