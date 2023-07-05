import asyncio
import logging
import asmp.asmp_pb2 as asmp
import zmq
from zmq.asyncio import Context, Socket

LOG = logging.getLogger(__name__)


# implements a client to the EVI, simulates being a Unity
# IMPORTANT: code was partly taken from unity.py class of evi
# and extended/changed

class EVIProtocol:

    context: Context
    connection: Socket
    current_id: int
    shutdown_event: asyncio.Event
    msg_queue_unity: asyncio.Queue
    msg_queue_evi: asyncio.Queue
    curr_updates: int

    def __init__(
        self,
        evi_port: int,
        shutdown_event: asyncio.Event,
        msg_queue_unity: asyncio.Queue,
        msg_queue_evi: asyncio.Queue,
    ) -> None:
        self.context = Context.instance()
        local_address = f"tcp://0.0.0.0:{evi_port}"
        self.shutdown_event = shutdown_event
        self.connection = self.context.socket(zmq.DEALER)
        self.connection.connect(local_address)
        self.current_id = 0
        self.msg_queue_unity = msg_queue_unity
        self.msg_queue_evi = msg_queue_evi
        self.curr_updates = 0

    async def request(self):
        # send a message with multiple ego vehicles to the EVI
        message = await self.msg_queue_unity.get()
        await self.connection.send_multipart(message)

        self.curr_updates = len(message)

        print(
            f"EVI connector sending message with {len(message)} requests"
        )

    async def get_reply(self):
        # handle multipart receive from EVI
        while self.curr_updates > 0:
            self.curr_updates -= 1

            print("EVI connector waiting for messages from EVI")
            received = await self.connection.recv_multipart()

            for m in received:
                message = asmp.Message()
                message.ParseFromString(m)

                if message.HasField("vehicle"):
                    print(f"Got Message from EVI: {message}")
                    for part in message.vehicle.commands:
                        if part.HasField("register_vehicle_command"):
                            part.register_vehicle_command.is_ego_vehicle = (
                                False
                            )
                        if part.HasField("unregister_vehicle_command"):
                            part.unregister_vehicle_command.is_ego_vehicle = (
                                False
                            )
                        if part.HasField("update_vehicle_command"):
                            part.update_vehicle_command.is_ego_vehicle = (
                                False
                            )
                await self.msg_queue_evi.put(message.SerializeToString())

            # put delimiter inbetween messages
            await self.msg_queue_evi.put("")

        print(
            f"EVI connector receving message with {len(received)} requests"
        )
