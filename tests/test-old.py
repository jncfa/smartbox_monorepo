import asyncio
import bleak
import json
import logging
import logging.config
import time

class BiostickerLogger():
    def __init__(self, logger, config) -> None:
        self.last_timestamps = {}
        self.logger = logger
        self.config = config

    def handle_data_imu(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got IMU data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_heart_rate(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got HR data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_temperature(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got Temperature data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_battery(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got Battery data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_respiratory_rate(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got RR1 data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_respiratory_rate_2(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got RR2 data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

    def handle_data_ecg(self, char, data: bytearray):
        new_timestamp = time.monotonic_ns()
        old_timestamp = self.last_timestamps.get(char, None)
        if (old_timestamp is not None): # ignore first fail
            self.logger.info(f'Got ECG data, took {(new_timestamp -old_timestamp)/1e6} ms')

        self.last_timestamps[char] = new_timestamp

async def connect_to_biosticker(config: dict):
    #try:
    logger = logging.getLogger("bluetooth")

    async with bleak.BleakClient(config["biosticker_simulated_mac_address"], adapter='hci0', disconnected_callback=(lambda client : logger.info("Device disconnected"))) as client:
        logger.info("Device connected")
    
        biostickerLogger = BiostickerLogger(logger, config)
        # select emulation mode
        await client.write_gatt_char(config["characteristics"]["Select Flag"]["uuid"], bytearray([0x0A]))
        
        # configure notification on every characteristic
        await client.start_notify(config["characteristics"]["IMU"]["uuid"], biostickerLogger.handle_data_imu)
        await client.start_notify(config["characteristics"]["Heart Rate"]["uuid"], biostickerLogger.handle_data_heart_rate)
        await client.start_notify(config["characteristics"]["Temperature"]["uuid"], biostickerLogger.handle_data_temperature)
        await client.start_notify(config["characteristics"]["Battery"]["uuid"], biostickerLogger.handle_data_battery)
        await client.start_notify(config["characteristics"]["RR_1"]["uuid"], biostickerLogger.handle_data_respiratory_rate)
        await client.start_notify(config["characteristics"]["RR_2"]["uuid"], biostickerLogger.handle_data_respiratory_rate_2)
        await client.start_notify(config["characteristics"]["ECG"]["uuid"], biostickerLogger.handle_data_ecg)

        while (client.is_connected):
            await asyncio.sleep(10) # ping biosticker every ~10 seconds on the "ping flag" characteristic (the watchdog timer is 30s)
            await client.write_gatt_char(config["characteristics"]["Ping Flag"]["uuid"], bytearray([0x01]))
            
        

    #except Exception as e:
    #    logger.fatal(f"catched this: {e}")
    #    pass


async def main(config):
    #await connect_to_biosticker(config)
    await asyncio.gather(
        connect_to_biosticker(config),
        #connect_to_oximeter(config)
    )

if __name__ == "__main__":
    logging.config.fileConfig('logging.config')
    config = None

    with open('config.json') as f:
        config = json.load(f)

    asyncio.run(main(config), debug=True)