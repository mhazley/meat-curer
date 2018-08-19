import logging
import time
import smbus

# SHT31D default address.
SHT31_I2CADDR = 0x44

# SHT31D Registers
SHT31_MEAS_HIGHREP_STRETCH = 0x2C06
SHT31_MEAS_MEDREP_STRETCH = 0x2C0D
SHT31_MEAS_LOWREP_STRETCH = 0x2C10
SHT31_MEAS_HIGHREP = 0x2400
SHT31_MEAS_MEDREP = 0x240B
SHT31_MEAS_LOWREP = 0x2416
SHT31_READSTATUS = 0xF32D
SHT31_CLEARSTATUS = 0x3041
SHT31_SOFTRESET = 0x30A2
SHT31_HEATER_ON = 0x306D
SHT31_HEATER_OFF = 0x3066

SHT31_STATUS_DATA_CRC_ERROR = 0x0001
SHT31_STATUS_COMMAND_ERROR = 0x0002
SHT31_STATUS_RESET_DETECTED = 0x0010
SHT31_STATUS_TEMPERATURE_ALERT = 0x0400
SHT31_STATUS_HUMIDITY_ALERT = 0x0800
SHT31_STATUS_HEATER_ACTIVE = 0x2000
SHT31_STATUS_ALERT_PENDING = 0x8000

# I2C
I2C_DEVICE_BUS = 1


class SHT31(object):
    def __init__(self, address=SHT31_I2CADDR, i2c=I2C_DEVICE_BUS):
        self._logger = logging.getLogger(__name__)

        self.address = address

        # Create I2C device.
        self._device = smbus.SMBus(I2C_DEVICE_BUS)
        time.sleep(0.05)  # Wait the required time

    def _writeCommand(self, cmd):
        # self._device.write8(cmd >> 8, cmd & 0xFF)
        self._device.write_byte_data(self.address, cmd >> 8, cmd & 0xFF)

    def _readBytes(self, register, length):
        results = self._device.read_i2c_block_data(self.address, register, length)
        self._logger.debug("Read the following from register 0x%02X: %s",
                           register, results)
        return results

    def reset(self):
        self._writeCommand(SHT31_SOFTRESET)
        time.sleep(0.01)  # Wait the required time

    def clear_status(self):
        self._writeCommand(SHT31_CLEARSTATUS);

    def read_status(self):
        self._writeCommand(SHT31_READSTATUS);
        buffer = self._readBytes(0, 3)
        stat = buffer[0] << 8 | buffer[1]
        if buffer[2] != self._crc8(buffer[0:2]):
            return None
        return stat

    def is_data_crc_error(self):
        return bool(self.read_status() & SHT31_STATUS_DATA_CRC_ERROR)

    def is_command_error(self):
        return bool(self.read_status() & SHT31_STATUS_COMMAND_ERROR)

    def is_reset_detected(self):
        return bool(self.read_status() & SHT31_STATUS_RESET_DETECTED)

    def is_tracking_temperature_alert(self):
        return bool(self.read_status() & SHT31_STATUS_TEMPERATURE_ALERT)

    def is_tracking_humidity_alert(self):
        return bool(self.read_status() & SHT31_STATUS_HUMIDITY_ALERT)

    def is_heater_active(self):
        return bool(self.read_status() & SHT31_STATUS_HEATER_ACTIVE)

    def is_alert_pending(self):
        return bool(self.read_status() & SHT31_STATUS_ALERT_PENDING)

    def set_heater(self, doEnable=True):
        if doEnable:
            self._writeCommand(SHT31_HEATER_ON)
        else:
            self._writeCommand(SHT31_HEATER_OFF)

    def read_temperature_humidity(self):
        self._writeCommand(SHT31_MEAS_HIGHREP)
        time.sleep(0.015)
        buffer = self._readBytes(0, 6)

        if buffer[2] != self._crc8(buffer[0:2]):
            return (float("nan"), float("nan"))

        rawTemperature = buffer[0] << 8 | buffer[1]
        temperature = 175.0 * rawTemperature / 0xFFFF - 45.0

        if buffer[5] != self._crc8(buffer[3:5]):
            return (float("nan"), float("nan"))

        rawHumidity = buffer[3] << 8 | buffer[4]
        humidity = 100.0 * rawHumidity / 0xFFFF

        return (temperature, humidity)

    def read_temperature(self):
        (temperature, humidity) = self.read_temperature_humidity()
        return temperature

    def read_humidity(self):
        (temperature, humidity) = self.read_temperature_humidity()
        return humidity

    def _crc8(self, buffer):
        """ Polynomial 0x31 (x8 + x5 +x4 +1) """

        polynomial = 0x31;
        crc = 0xFF;

        index = 0
        for index in range(0, len(buffer)):
            crc ^= buffer[index]
            for i in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc = (crc << 1)
        return crc & 0xFF

def main():
    logging.basicConfig(level='INFO')
    sht31 = SHT31()

    while True:
        print(sht31.read_temperature_humidity())
        time.sleep(2)
        
if __name__ == '__main__':
    main()
