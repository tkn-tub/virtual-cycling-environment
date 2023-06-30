#pi is server
import sys
import time
import message 
import asmp_pb2 as asmp
import zmq



class Communication:

    def __init__(self, evi_port, pi_port,**ignored_kwargs):
        assert pi_port is not None

        self._local_addr = "tcp://{}:{}".format('0.0.0.0', pi_port)
        self._context = zmq.Context()
        self._connection = None
        self._evi_addr = evi_port

    def init(self):
        """
        Set up connection dependent data.
        """
        self._connection = self._context.socket(zmq.REP)
        self._connection.bind(self._local_addr)
        self._connection.RCVTIMEO = 1000
        print("Socket for Pi set up to listen on '%s'.", self._local_addr)

    def sent_evi_reply(self):
        """
        Send answer to EVI
        """
        self._connection.send(b"Received data")

    def receive_signal_message(self):
        """
        Wait for data from EVI.
        """
        print("Waiting for data from EVI.")
        try:
            request_bytes = self._connection.recv_multipart()
        except zmq.Again:
            return None

        hapticsignals_signals = []
        for frame in request_bytes:
            ready_msg = asmp.Message()
            ready_msg.ParseFromString(frame)

            if ready_msg.HasField('hapticsignals'):
                hapticsignals_signals.append(ready_msg.hapticsignals.signals)

        if hapticsignals_signals:
            print("Received %d hapticsignals signals", len(hapticsignals_signals))

            for i, event_command in enumerate(hapticsignals_signals):
                event_message = asmp.Message()
                event_message.hapticsignals.signals.CopyFrom(event_command)
                print(event_message)

            x=event_message.hapticsignals.signals.dangers;
            y=event_message.hapticsignals.signals.vibrations;
            z=event_message.hapticsignals.signals.pattern;
            m=message.Message(y,x,z)
            return m
        return None     
        

