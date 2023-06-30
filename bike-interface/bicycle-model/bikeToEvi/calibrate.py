#!/usr/bin/env python3

import configparser
import time

import tacx

def main():
    filename = "calibration.ini"
    bt = tacx.BlackTrack()

    try:
        bt.start()

        repeat = 10
        wait = 0.5 # in s

        input("Steer full left and press enter")

        left = 0
        for i in range(repeat):
            with bt.lock:
                left += bt.raw_angle
                print("Got %f" % bt.raw_angle)
            time.sleep(wait)
        left /= repeat
        print("Average %f" % left)

        input("Steer full right and press enter")

        right = 0
        for i in range(repeat):
            with bt.lock:
                right += bt.raw_angle
                print("Got %f" % bt.raw_angle)
            time.sleep(wait)
        right /= repeat
        print("Average %f" % right)

        input("Steer center and press enter")

        center = 0
        for i in range(repeat):
            with bt.lock:
                center += bt.raw_angle
                print("Got %f" % bt.raw_angle)
            time.sleep(wait)
        center /= repeat
        print("Average %f" % center)

        calibration = configparser.ConfigParser()
        calibration["BlackTrack"] = {"left": left,
                                    "center": center,
                                    "right": right}
        with open(filename, "w") as f:
            calibration.write(f)
            print("Calibration data has been written to {}. Thank you.".format(filename))

    finally:
        print("closing connection to BlackTrack")
        bt.stop()
        bt.join()



if __name__ == '__main__':
    main()