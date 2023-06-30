import unittest

import asmp.asmp_pb2 as asmp
from asmp.asmp import session_pb2 as session
from asmp.asmp import vehicle_pb2 as vehicle
from evi import validator
from evi.util import to_uint


class TestValidator(unittest.TestCase):

    def test_message_is_valid(self):
        message = asmp.Message()
        self.assertFalse(validator.message_is_valid(message))

    def test_session_is_valid(self):
        session_message = session.Message()
        self.assertFalse(validator.session_message_is_valid(session_message))

        session_message.initialize.time_s = 0.0
        self.assertTrue(validator.session_message_is_valid(session_message))

        session_message.teardown.SetInParent()
        self.assertTrue(validator.session_message_is_valid(session_message))

    def test_command_block_is_valid(self):
        cmd_block = vehicle.Message()

        self.assertTrue(validator.command_block_is_valid(cmd_block))
        cmd = cmd_block.commands.add()
        cmd.register_vehicle_command.vehicle_id = to_uint("someid1")
        cmd.register_vehicle_command.state.position.road_id = to_uint("someid2")
        self.assertTrue(validator.command_is_valid(cmd))
        self.assertTrue(validator.command_block_is_valid(cmd_block))
        cmd = cmd_block.commands.add()
        cmd.register_vehicle_command.vehicle_id = to_uint("someid3")
        cmd.register_vehicle_command.state.position.road_id = to_uint("someid4")
        self.assertTrue(validator.command_block_is_valid(cmd_block))

    def test_command_is_valid(self):
        # Unitialized Command -> invalid
        cmd = vehicle.Command()
        self.assertFalse(validator.command_is_valid(cmd))

        # Register Command
        # missing road_id -> invalid
        cmd = vehicle.Command()
        cmd.register_vehicle_command.vehicle_id = to_uint("someid")
        self.assertFalse(validator.command_is_valid(cmd))
        # missing vehicle_id -> invalid
        cmd = vehicle.Command()
        cmd.register_vehicle_command.state.position.road_id = to_uint("someid")
        self.assertFalse(validator.command_is_valid(cmd))
        cmd = vehicle.Command()
        # both IDs present -> valid
        cmd.register_vehicle_command.vehicle_id = to_uint("someid")
        cmd.register_vehicle_command.state.position.road_id = to_uint("someid")
        self.assertTrue(validator.command_is_valid(cmd))

        # Unregister Command
        # vehicle_id -> valid
        cmd = vehicle.Command()
        cmd.unregister_vehicle_command.vehicle_id = to_uint("someid")
        self.assertTrue(validator.command_is_valid(cmd))

        # Update Command
        # missing road_id -> invalid
        cmd = vehicle.Command()
        cmd.update_vehicle_command.vehicle_id = to_uint("someid")
        self.assertFalse(validator.command_is_valid(cmd))
        # missing vehicle_id -> invalid
        cmd = vehicle.Command()
        cmd.update_vehicle_command.state.position.road_id = to_uint("someid")
        self.assertFalse(validator.command_is_valid(cmd))
        # both IDs present -> valid
        cmd = vehicle.Command()
        cmd.update_vehicle_command.vehicle_id = to_uint("someid")
        cmd.update_vehicle_command.state.position.road_id = to_uint("someid")
        self.assertTrue(validator.command_is_valid(cmd))

    def test_register_vehicle_command_is_valid(self):
        cmd = vehicle.RegisterVehicleCommand()
        cmd.state.position.road_id = to_uint("someid")
        self.assertFalse(validator.register_vehicle_command_is_valid(cmd))

        cmd.ClearField('vehicle_id')
        self.assertFalse(validator.register_vehicle_command_is_valid(cmd))

        cmd.vehicle_id = to_uint("someid")
        self.assertTrue(validator.register_vehicle_command_is_valid(cmd))

    def test_unregister_vehicle_command_is_valid(self):
        cmd = vehicle.UnregisterVehicleCommand()
        self.assertFalse(validator.unregister_vehicle_command_is_valid(cmd))

        cmd.ClearField('vehicle_id')
        self.assertFalse(validator.unregister_vehicle_command_is_valid(cmd))

        cmd.vehicle_id = to_uint("someid")
        self.assertTrue(validator.unregister_vehicle_command_is_valid(cmd))

    def test_update_vehicle_command_is_valid(self):
        cmd = vehicle.UpdateVehicleCommand()
        cmd.state.position.road_id = to_uint("someid")
        self.assertFalse(validator.update_vehicle_command_is_valid(cmd))

        cmd.ClearField('vehicle_id')
        self.assertFalse(validator.update_vehicle_command_is_valid(cmd))

        cmd.vehicle_id = to_uint("someid")
        self.assertTrue(validator.update_vehicle_command_is_valid(cmd))

    def test_vehicle_state_is_valid(self):
        state = vehicle.VehicleState()
        state.position.road_id = to_uint("someid")

        self.assertTrue(validator.vehicle_state_is_valid(state))
        state.speed_mps = -10
        self.assertTrue(validator.vehicle_state_is_valid(state))
        state.speed_mps = 10
        self.assertTrue(validator.vehicle_state_is_valid(state))
        state.speed_mps = 0
        self.assertTrue(validator.vehicle_state_is_valid(state))

    def test_vehicle_position_is_valid(self):
        pos = vehicle.VehiclePosition()
        self.assertFalse(validator.vehicle_position_is_valid(pos))

        # no road id
        pos.ClearField('road_id')
        pos.s_frac = 0.0
        self.assertFalse(validator.vehicle_position_is_valid(pos))
        pos.Clear()

        # negative s_frac
        pos.road_id = to_uint("someid")
        pos.s_frac = -1.0
        self.assertFalse(validator.vehicle_position_is_valid(pos))
        pos.s_frac = 1.1
        self.assertFalse(validator.vehicle_position_is_valid(pos))
        pos.Clear()

        # negative lane/d_frac
#        pos.road_id = to_uint("someid")
#        pos.d_frac = -1.0
#        pos.s_frac = 0.0
#        self.assertFalse(validator.vehicle_position_is_valid(pos))
#        # too big lane/d_frac
#        pos.d_frac = 1.1
#        self.assertFalse(validator.vehicle_position_is_valid(pos))
#        pos.Clear()

        # valid data
        pos.road_id = to_uint("someid")
        pos.s_frac = 0.0
        self.assertTrue(validator.vehicle_position_is_valid(pos))
        pos.Clear()

    def test_message_block_is_valid(self):
        pass


if __name__ == '__main__':
    unittest.main(buffer=True)
