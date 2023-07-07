import asyncio
import logging
import asmp.asmp_pb2 as asmp
import time
import zmq
from zmq.asyncio import Context, Socket
import binascii

LOG = logging.getLogger(__name__)

# implements a server to the 3D Environment
# IMPORTANT: code was partly taken from unity.py class of evi
# and extended/changed


class Env3dProtocol:

    context: Context
    connection: Socket
    current_id: int
    shutdown_event: asyncio.Event
    # for Messages from the 3D Environment
    msg_queue_env3d: asyncio.Queue
    # for Messages from EVI
    msg_queue_evi: asyncio.Queue
    msg_queue_commands: asyncio.Queue
    client_updated: []
    ego_vehicle_list: []
    number_of_env3ds: int
    curr_time: float
    curr_updates: int
    ego_ids: []

    def __init__(
        self,
        env3d_port: int,
        shutdown_event: asyncio.Event,
        msg_queue_env3d: asyncio.Queue,
        msg_queue_evi: asyncio.Queue,
        number_of_env3ds: int
    ) -> None:
        self.context = Context.instance()
        local_address = f"tcp://0.0.0.0:{env3d_port}"
        self.shutdown_event = shutdown_event
        # Use a router/dealer socket to identify clients and who send what
        self.connection = self.context.socket(zmq.ROUTER)
        self.connection.bind(local_address)
        self.current_id = 0
        self.msg_queue_env3d = msg_queue_env3d
        self.msg_queue_evi = msg_queue_evi
        self.msg_queue_commands = asyncio.Queue()
        self.ego_vehicle_list = []
        self.number_of_env3ds = number_of_env3ds
        self.curr_time = 0.0
        self.curr_updates = 0
        self.client_updated = []
        self.updates = []
        self.ego_ids = []

    # Wait for first messages from all 3DEnv instances,
    # and process these messages
    async def serve_intialize(self):
        print(
            "3DEnv connector is waiting for first messages "
            "from 3DEnv instances…"
        )
        while not self.curr_updates == self.number_of_env3ds:
            message_bytes = await self.connection.recv_multipart()
            clientAdress = message_bytes[0]
            # print("test")
            # hex_data = binascii.hexlify(clientAdress)
            # str_data = hex_data.decode('utf-8')
            # print(str_data)

            # decode
            message = asmp.Message()
            message.ParseFromString(message_bytes[1])
            # print("Got Message from 3DEnv: %s", message)

            # get vehicle ID
            commands = message.vehicle.commands

            for command in commands:
                # all_fields = set([field.name for field in command._fields])
                # if "register_vehicle_command" in all_fields:
                if command.HasField('register_vehicle_command'):
                    vehicle_id = command.register_vehicle_command.vehicle_id

                    if vehicle_id not in self.ego_ids:
                        self.ego_ids.append(vehicle_id)
                        self.client_updated.append((clientAdress, vehicle_id))
                        self.ego_vehicle_list.append((
                            clientAdress, message, vehicle_id
                        ))
                        self.curr_updates += 1
                    else:
                        # delete entries
                        # find element position
                        position = list(map(
                            lambda x: x[2],
                            self.ego_vehicle_list
                        )).index(vehicle_id)
                        # delete element
                        self.ego_vehicle_list.pop(position)
                        # find element position
                        position = list(map(
                            lambda x: x[1],
                            self.client_updated
                        )).index(vehicle_id)
                        # delete element
                        self.client_updated.pop(position)
                        # add with new position
                        self.client_updated.append(
                            (clientAdress, vehicle_id)
                        )
                        self.ego_vehicle_list.append(
                            (clientAdress, message, vehicle_id)
                        )

                    print(
                        f"3DEnv connector got Message from 3DEnv: {message}"
                    )

        for (address, veh_msg, veh_id) in self.ego_vehicle_list:
            self.updates.append((address, veh_msg))

        # direct ego position exchange
        ego_message = []
        for (client, vehicle_id) in self.client_updated:
            adress = client
            ego_message.clear()
            ego_message.append(adress)
            ego_message.append(b'')

            # add other ego vehicles
            for (client_adress, msg, ego_id) in self.ego_vehicle_list:
                # all_fields = set([field.name for field in msg._fields])
                if vehicle_id != ego_id:
                    # if "register_vehicle_command" in all_fields:
                    if command.HasField('register_vehicle_command'):
                        command.register_vehicle_command.is_ego_vehicle = True
                        # print("Got Message from EVI: %s", part)
                ego_message.append(msg.SerializeToString())

            print(
                "3DEnv connector sending ego update message "
                f"with {len(ego_message)} replies"
            )
            # print("Send Message to 3DEnv: %s", final_message)

            # await asyncio.create_task(self._send_message_set(ego_message))

        await self.msg_queue_env3d.put(await self.construct_evi_message_proto(
            self.updates, 0.0, self.number_of_env3ds
        ))

        self.curr_updates = 0

    # Process messages from multiple 3DEnv instances
    async def serve_only(self):
        print(
            "3DEnv connector is waiting for messages "
            "from 3DEnv instances…"
        )
        self.client_updated.clear()
        self.curr_time = time.perf_counter()
        stop = False

        while (
                self.curr_updates != self.number_of_env3ds
                and abs(self.curr_time - time.perf_counter()) < 0.05
                and not stop
        ):
            try:
                # wait for at least one 3DEnv to send update message
                if self.curr_updates == 0:
                    message_bytes = await self.connection.recv_multipart()
                else:
                    message_bytes = await asyncio.wait_for(
                        self.connection.recv_multipart(),
                        timeout=0.05
                    )
            except asyncio.TimeoutError:
                print("Timeout")
                stop = True

            if not stop:
                clientAdress = message_bytes[0]
                print(clientAdress)
                # decode
                message = asmp.Message()
                message.ParseFromString(message_bytes[1])

                # get vehicle ID
                commands = message.vehicle.commands

                for command in commands:
                    vehicle_id = command.update_vehicle_command.vehicle_id

                if (clientAdress, vehicle_id) not in self.client_updated:
                    self.client_updated.append((clientAdress, vehicle_id))
                    self.curr_updates += 1

                if self.curr_updates == 1:
                    self.curr_time = time.perf_counter()

                print(f"3DEnv connector got Message from 3DEnv: {message}")

                if vehicle_id in self.ego_ids:
                    # update ego vehicle position message
                    # find element position
                    position = list(map(
                        lambda x: x[2],
                        self.ego_vehicle_list
                    )).index(vehicle_id)
                    # delete element
                    self.ego_vehicle_list.pop(position)
                    # add with new position
                    self.ego_vehicle_list.append(
                        (clientAdress, message, vehicle_id)
                    )

                self.updates.append((clientAdress, message))

        # direct ego position exchange
        ego_message = []
        for (client, vehicle_id) in self.client_updated:
            adress = client
            ego_message.clear()
            ego_message.append(adress)
            ego_message.append(b'')

            # add other ego vehicles
            for (client_adress, msg, id) in self.ego_vehicle_list:
                # all_fields = set([field.name for field in msg._fields])
                if vehicle_id != id:
                    # if "register_vehicle_command" in all_fields:
                    if command.HasField('register_vehicle_command'):
                        # msg.register_vehicle_command.is_ego_vehicle=True
                        # print("Got Message from EVI: %s", part)
                        command.register_vehicle_command.is_ego_vehicle = True
                    # if "unregister_vehicle_command" in all_fields:
                    if command.HasField('unregister_vehicle_command'):
                        # msg.unregister_vehicle_command.is_ego_vehicle=True
                        command.unregister_vehicle_command.is_ego_vehicle = (
                            True
                        )
                        # print("Got Message from EVI: %s", part)
                    # if "update_vehicle_command" in all_fields:
                    if command.HasField('update_vehicle_command'):
                        # msg.update_vehicle_command.is_ego_vehicle=True
                        command.update_vehicle_command.is_ego_vehicle = True
                        # print("Got Message from EVI: %s", part.update_vehicle_command.is_ego_vehicle)
                    ego_message.append(msg.SerializeToString())

            print(
                "3DEnv connector sending ego update "
                f"message with {len(ego_message)} replies"
            )
            # print("Send Message to 3DEnv: %s", final_message)

            # await asyncio.create_task(self._send_message_set(ego_message))

        # construct message out of all and put in queue for evi
        message = await self.construct_evi_message_proto(
            self.updates,
            None,
            self.number_of_env3ds
        )

        await self.msg_queue_env3d.put(message)

        self.curr_updates = 0

    # Construct EVI suitable update message
    async def construct_evi_message_proto(
            self,
            message_list,
            time_s,
            number_messages
    ):
        # go through message list updated
        update_message = asmp.Message()
        if time_s is not None:
            update_message.vehicle.time_s = time_s
        commands = update_message.vehicle.commands

        num = 0
        already_updated = []
        delete = []
        result = []

        for tuple_curr in message_list:
            # print(tuple_curr)
            if num < number_messages:
                if tuple_curr[0] not in already_updated:
                    delete.append(tuple_curr[1])
                    already_updated.append(tuple_curr[0])

                    add_vehicles = tuple_curr[1].vehicle.commands
                    for add_vehicle in add_vehicles:
                        add_command = commands.add()
                        if add_vehicle.HasField("register_vehicle_command"):
                            add_command.register_vehicle_command.MergeFrom(
                                add_vehicle.register_vehicle_command
                            )
                        if add_vehicle.HasField("unregister_vehicle_command"):
                            add_command.unregister_vehicle_command.MergeFrom(
                                add_vehicle.unregister_vehicle_command
                            )
                        if add_vehicle.HasField("update_vehicle_command"):
                            add_command.update_vehicle_command.MergeFrom(
                                add_vehicle.update_vehicle_command
                            )

                    num += 1

        # delete item in updates list

        for y in delete:
            position = list(map(lambda x: x[1], self.updates)).index(y)
            # delete element
            self.updates.pop(position)

        result.append(update_message.SerializeToString())

        return result

    # Distribute EVI replies to all 3DEnvs
    async def reply(self):
        print("Start replying to 3DEnv")
        # message_strings = []
        final_message = []

        evi_message = []

        # construct message to 3DEnv
        # Fake do while loop
        continue_loop = True
        while continue_loop:
            curr_reply = await self.msg_queue_evi.get()
            if curr_reply == "":
                continue_loop = False
            else:
                evi_message.append(curr_reply)

        # Send reply to each client
        for (client, vehicle_id) in self.client_updated:
            ego_message = []
            # add other ego vehicles
            for (client_adress, msg, id) in self.ego_vehicle_list:
                if vehicle_id != id:
                    ego_message.append(msg.SerializeToString())

            intermediate = ego_message + evi_message
            adress = client
            final_message.clear()
            final_message.append(adress)
            final_message.append(b'')

            final_message = final_message + intermediate

            await asyncio.create_task(self._send_message_set(final_message))
            # print(
            #     f"Send Message to 3DEnv: {final_message} "
            #     f"with length {len(final_message)}"
            # )

    async def _send_message_set(self, message_strings):
        await self.connection.send_multipart(message_strings)
