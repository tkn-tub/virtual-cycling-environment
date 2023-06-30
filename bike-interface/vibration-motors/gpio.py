import time
import sys
import RPi.GPIO as GPIO
import message
# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BCM)

# Pin 18 (GPIO 19) auf Input setzen is left
GPIO.setup(19, GPIO.OUT)

# Pin 11 (GPIO 26) auf Output setzen is right
GPIO.setup(26, GPIO.OUT)

def vibration(x,y,z):

    side=x
    level=y
    pattern=z
    if pattern=="STANDARD":
        count=66
        if level > 0:
            while count > 0:
                count=count-1
                if side=="LEFT" or side=="BOTH":
                    GPIO.output(26, GPIO.HIGH)
                elif side=="RIGHT" or side=="BOTH":
                    GPIO.output(19, GPIO.HIGH)

                # Wait 10ms
                time.sleep(0.01)

                if side=="LEFT" or side=="BOTH":
                    GPIO.output(26,GPIO.LOW)
                elif side=="RIGHT" or side=="BOTH":
                    GPIO.output(19,GPIO.LOW)

                if count==33 or count==1:
                    time.sleep(0.3*level)
                else:
                    time.sleep(0.01)
