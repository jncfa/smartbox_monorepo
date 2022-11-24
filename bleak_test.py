import asyncio
from bleak import BleakClient, BleakGATTCharacteristic

address = "E8:E1:54:85:AA:61"
CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

async def handle_data(char: BleakGATTCharacteristic, data: bytearray):
    print("got here")
    raise RuntimeError("forced error")
    
async def main(address):
    async with BleakClient(address) as client:
        print("initialized")
        await client.start_notify(CHAR_UUID, handle_data)
        await asyncio.sleep(60)
        
        

asyncio.run(main(address))