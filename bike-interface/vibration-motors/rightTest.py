import sys
import time
import argparse
import logging
import RPi.GPIO as GPIO

# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BCM)

# Pin 18 (GPIO 19) auf Input setzen is left
GPIO.setup(19, GPIO.OUT)

# Pin 11 (GPIO 26) auf Output setzen is right
GPIO.setup(26, GPIO.OUT)

def main(right):
    y=right

    
    for m in range(y):
        count=66
        while count > 0:
            count=count-1
            GPIO.output(19, GPIO.HIGH)
            # Wait 1000ms
            time.sleep(0.01)
            GPIO.output(19,GPIO.LOW)
            
            if count==33 or count==1:
                time.sleep(0.4)
            else:
                time.sleep(0.01)
    
if __name__ == '__main__':
    pi_parser = argparse.ArgumentParser(add_help=False)
    pi_parser.add_argument('--right', dest='r', type=int, help='number of vibrations on that side')
    args = pi_parser.parse_args()
    main(right=args.r)

