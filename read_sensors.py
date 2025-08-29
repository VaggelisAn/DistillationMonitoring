import time
import board
import busio
import digitalio
import adafruit_shtc3
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import predict_quality 
import numpy as np
import matplotlib.pyplot as plt

# Init I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Init SHTC3
sht = adafruit_shtc3.SHTC3(i2c)

# Init ADS1015
ads = ADS.ADS1015(i2c)
chan = AnalogIn(ads, ADS.P0)  # MQ-3 on A0

# LED Pin (GPIO17 / physical pin 11)
LED_PIN = board.D17  # Pin for LED indicator

# ----- Write LED -----
def write_led(HIGH=True):
    led = digitalio.DigitalInOut(LED_PIN)
    led.direction = digitalio.Direction.OUTPUT
    if (HIGH == True):
        led.value = True
    else:
        led.value = False

    time.sleep(0.1)

# ----- Read Sensors -----
def read_sensors():
    temperature, humidity = sht.measurements
    alcohol_voltage = chan.voltage  # raw voltage

    return temperature, alcohol_voltage

# ----- Main Loop -----
if __name__ == "__main__":
    while True:
        temp, alcohol = read_sensors()
        print(f"Temperature: {temp:.2f} °C")
        print(f"Alcohol sensor: {alcohol*3300/1024}ppm")
        time.sleep(1)