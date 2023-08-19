import subprocess
import RPi.GPIO as GPIO
import time as t

GPIO.setwarnings(False)

def get_cpu_temperature():

    try:
        temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
        temperature = float(temp.replace('temp=', '').replace('\'C\n', ''))
        return temperature
    except Exception as e:
        print("Wystąpił błąd:", e)
        return None

temperature = get_cpu_temperature()

while temperature is not None:
    try:
        tmp = get_cpu_temperature()
        if tmp > 30:
            print(f"CPU temp1: {tmp:.0f}")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(24, GPIO.OUT)
            GPIO.output(24, GPIO.HIGH)

        elif tmp <=30:
            print(f"CPU temp2: {tmp:.0f}")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(24, GPIO.OUT)
            GPIO.output(24, GPIO.LOW)
            GPIO.cleanup()

        else:
            print("Can't read CPU temp")
    except ValueError:
        print("Can't read CPU temp")
    t.sleep(60)
