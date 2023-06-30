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

def main(both):
    z=both

    for o in range(z):
        count=66
        while count > 0:
            count=count-1
            GPIO.output(26, GPIO.HIGH)
            GPIO.output(19, GPIO.HIGH)

            # Wait 1000ms
            time.sleep(0.01)

            GPIO.output(26,GPIO.LOW)
            GPIO.output(19,GPIO.LOW)

            if count==33 or count==1:
                time.sleep(0.4)
            else:
                time.sleep(0.01)

if __name__ == '__main__':
    pi_parser = argparse.ArgumentParser(add_help=False)
    pi_parser.add_argument('--both', dest='b', type=int, help='number of vibrations on that side')
    args = pi_parser.parse_args()
    main(both=args.b)

