import sys
import message
import time
import argparse
import zmq
import communication
import threading
import queue
import gpio

def main(evi_port, pi_port):
    """Run the vibration programm."""
    _pi_interface=communication.Communication(evi_port, pi_port)
    msg_queue = queue.Queue()
    shutdown = threading.Event()

    t1 = threading.Thread(target=communicationThread,args=(_pi_interface,msg_queue, shutdown))
    t2 = threading.Thread(target=vibrations,args=(msg_queue, shutdown))
    print("Press CRTL+C to close program.")
    t1.start()
    t2.start()

    try:
        time.sleep(10000000)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        shutdown.set()
        raise

#task 1
def communicationThread(_pi_interface,msg_queue, shutdown):
    """Read messages from ZMQ."""
    #connect to EVI
    _pi_interface.init()

    while not shutdown.is_set():
        #print("waiting for message")
        msg = _pi_interface.receive_signal_message()
        #print("received")
        if msg is not None:
            #print("putting msg into queue")
            msg_queue.put(msg)
        else:
            #print("got invalid message")
            continue
        #print("sending reply")
        _pi_interface.sent_evi_reply()
        #print("reply sent")

#task 2(read from buffer and cause vibrations)
def vibrations(msg_queue, shutdown):
    """Cause vibration."""
    isEmpty=True
    
    while not shutdown.is_set():
        #print("next try")
        # get item from queue
        try:
            msg = msg_queue.get(timeout=3)
        except queue.Empty:
            print("queue timeout...")
            continue
        x=msg.getSide()
        y=msg.getLevel()
        z=msg.getPattern()
        # check if valid item received from queue
        if x!="NONE":
            # if so, vibrate
            #print("start vibrating")
            gpio.vibration(x,y,z)
            #print("end vibrating")
        else:
            print("Got NONE message")
    print("Vibration thread shutting down")


if __name__ == '__main__':
    pi_parser = argparse.ArgumentParser(add_help=False)
    pi_parser.add_argument('--evi-port', dest='eviport', type=int, help='Port of evi')
    pi_parser.add_argument('--pi-port', dest='piport', type=int, help='Port of pi')
    args = pi_parser.parse_args()
    main(evi_port=args.eviport, pi_port=args.piport)

