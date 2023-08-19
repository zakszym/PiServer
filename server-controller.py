import smbus
import os
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time as t
import subprocess
import RPi.GPIO as GPIO

# Define the I2C address of your display (default: 0x3C)
I2C_ADDR = 0x3C

# Initialize I2C communication
serial = i2c(port=1, address=I2C_ADDR)

# Create a SH1106 OLED display instance
device = sh1106(serial, rotate=0)  # Set 'rotate' based on your display orientation

# Create a blank image
width = device.width
height = device.height
image = Image.new('1', (width, height))

# Get a drawing object to draw on the image
draw = ImageDraw.Draw(image)

# Load a font
font = ImageFont.load_default()

# Display text
#draw.text((0, 0), 'Hello,', font=font, fill=255)

GPIO.setwarnings(False)

# Display the image
device.display(image)

# Config Register (R/W)
_REG_CONFIG                 = 0x00
# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE           = 0x01

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE             = 0x02

# POWER REGISTER (R)
_REG_POWER                  = 0x03

# CURRENT REGISTER (R)
_REG_CURRENT                = 0x04

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION            = 0x05

class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    """Constants for ``mode``"""
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous


class INA219:
    def __init__(self, i2c_bus=1, addr=0x40):
        self.bus = smbus.SMBus(i2c_bus);
        self.addr = addr

        # Set chip to known config values to start
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2A()

    def read(self,address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return ((data[0] * 256 ) + data[1])

    def write(self,address,data):
        temp = [0,0]
        temp[1] = data & 0xFF
        temp[0] =(data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr,address,temp)

    def set_calibration_32V_2A(self):
        """Configures to INA219 to be able to measure up to 32V and 2A of current. Counter
           overflow occurs at 3.2A.
           ..note :: These calculations assume a 0.1 shunt ohm resistor is present
        """

        self._current_lsb = .1  # Current LSB = 100uA per bit

        self._cal_value = 4096

        self._power_lsb = .002  # Power LSB = 2mW per bit

        # Set Calibration register to 'Cal' calculated above
        self.write(_REG_CALIBRATION,self._cal_value)

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | \
                      self.gain << 11 | \
                      self.bus_adc_resolution << 7 | \
                      self.shunt_adc_resolution << 3 | \
                      self.mode
        self.write(_REG_CONFIG,self.config)

    def getShuntVoltage_mV(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def getBusVoltage_V(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        self.read(_REG_BUSVOLTAGE)
        return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004

    def getCurrent_mA(self):
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def getPower_W(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb

if __name__=='__main__':

    def get_cpu_temperature():

        try:
            temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
            temperature = float(temp.replace('temp=', '').replace('\'C\n', ''))
            return temperature
        except Exception as e:
            draw.text((0, 30), 'Error occured!', font=font, fill=255)
            print("Error occured!", e)
            return None

    temperature = get_cpu_temperature()

        # Create an INA219 instance.
    ina219 = INA219(addr=0x42)
    while True:
        bus_voltage = ina219.getBusVoltage_V()             # voltage on V- (load side)
        shunt_voltage = ina219.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
        current = ina219.getCurrent_mA()                   # current in mA
        power = ina219.getPower_W()                        # power in W
        p = (bus_voltage - 6)/2.4*100
        if(p > 100):p = 100
        if(p < 0):p = 0
        tmp = get_cpu_temperature()
        image = Image.new('1', (width, height))
        draw = ImageDraw.Draw(image)
        draw.text((0, 00), 'KAMI SERVER CONTROLER: ' + str(tmp), font=font, fill=255)
        draw.text((0, 10), 'CPU Temp:: ' + str(tmp), font=font, fill=255)
        draw.text((0, 20), 'Load Volt.: ' + str("{:6.3f} V".format(bus_voltage)), font=font, fill=255)
        draw.text((0, 30), 'Current: ' + str("{:9.6f} A".format(current/1000)), font=font, fill=255)
        draw.text((0, 40), 'Power: ' + str("{:6.3f} W".format(power)), font=font, fill=255)
        draw.text((0, 50), 'Percent: ' + str("{:3.1f}%".format(p)), font=font, fill=255)
        device.display(image)
        if tmp > 30:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(24, GPIO.OUT)
            GPIO.output(24, GPIO.HIGH)

        elif tmp <=30:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(24, GPIO.OUT)
            GPIO.output(24, GPIO.LOW)
            GPIO.cleanup()

        else:
            draw.text((0, 30), 'Cant read CPU temp', font=font, fill=255)
            print("Can't read CPU temp")
        t.sleep(2)

