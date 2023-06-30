"""
ASM message validation functions.
"""


def message_is_valid(message):
    return (
        message.WhichOneof("message_oneof") is not None
        and (
            not message.HasField("session")
            or session_message_is_valid(message.session)
        )
        and (
            not message.HasField("vehicle")
            or command_block_is_valid(message.vehicle)
        )
    )


def session_message_is_valid(session_message):
    return session_message.WhichOneof("message_oneof") is not None


def command_block_is_valid(command_block):
    return all(command_is_valid(command) for command in command_block.commands)


def command_is_valid(command):
    return (
        command.WhichOneof("command_oneof") is not None
        and (
            not command.HasField("register_vehicle_command")
            or register_vehicle_command_is_valid(
                command.register_vehicle_command
            )
        )
        and (
            not command.HasField("unregister_vehicle_command")
            or unregister_vehicle_command_is_valid(
                command.unregister_vehicle_command
            )
        )
        and (
            not command.HasField("update_vehicle_command")
            or update_vehicle_command_is_valid(command.update_vehicle_command)
        )
    )


def register_vehicle_command_is_valid(command):
    return command.HasField("vehicle_id") and vehicle_state_is_valid(
        command.state
    )


def unregister_vehicle_command_is_valid(command):
    return command.HasField("vehicle_id")


def update_vehicle_command_is_valid(command):
    return command.HasField("vehicle_id") and vehicle_state_is_valid(
        command.state
    )


def vehicle_state_is_valid(state):
    return vehicle_position_is_valid(state.position)


def vehicle_position_is_valid(position):
    return position.HasField("road_id") and (0 <= position.s_frac <= 1)
