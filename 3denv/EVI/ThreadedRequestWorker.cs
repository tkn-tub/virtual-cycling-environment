using Godot;
using System;
using System.Collections.Concurrent;
using System.Threading;

using NetMQ;
using NetMQ.Sockets;
using System.Collections.Generic;
using Google.Protobuf;
using System.Diagnostics;
using Asmp.Vehicle;



public class ThreadedRequestWorker : Node, IThreadedNetWorker
{

	[Signal] public delegate void newUpdateArrived();
	
	
	private List<IObserver<Dictionary<uint, VehicleData>>> observers = new List<IObserver<Dictionary<uint, VehicleData>>>();

	// NetMQ Socket to connect to EVI
	private DealerSocket dealerSock;

	// Worker Thread for communication
	private System.Threading.Thread netThread;

	// Address of the EVI to connect to
	private string EVIAdress;

	private double xOffset, yOffset;

	// Queue for data to send to EVI
	private Asmp.Message NextFrameUpdate = new Asmp.Message();


	// Queue for data received from EVI
	private BlockingCollection<Asmp.Message> recvQueue;
	public Dictionary<uint, VehicleData> registerCommands = new Dictionary<uint, VehicleData>();
	public Dictionary<uint, VehicleData> unregisterCommands = new Dictionary<uint, VehicleData>();
	public Dictionary<uint, VehicleData> updateVehicleCommands = new Dictionary<uint, VehicleData>();

	// These are not currently used (??)
	public Dictionary<uint, VehicleData> doorStates = new Dictionary<uint, VehicleData>();
	public Dictionary<uint, VehicleData> otherVehicleCommands = new Dictionary<uint, VehicleData>();


	public ThreadedRequestWorker(string pEVIAdress, double _xOffset, double _yOffset)
	{
		xOffset = _xOffset;
		yOffset = _yOffset;

		AsyncIO.ForceDotNet.Force();

		EVIAdress = pEVIAdress;

		recvQueue = new BlockingCollection<Asmp.Message>();
		
		dealerSock = new DealerSocket(EVIAdress);

		netThread = new System.Threading.Thread(new ThreadStart(WorkNetThread));
		netThread.Start();
	}

	bool NewFrameAvailable = false;

	bool FrameWasUpdated = false;

	//sets the next frame which is send to the evi
	public bool SaveNextFrame(Asmp.Message data)
	{
		if (!NextFrameUpdate.ToString().Contains("registerVehicleCommand") || FrameWasUpdated)
		{
			NewFrameAvailable = true;
			FrameWasUpdated = false;
			NextFrameUpdate = data;
			return true;
		}

		return false;
	}

	public bool HasResults()
	{
		return recvQueue.Count > 0;
	}

	public Asmp.Message Recv()
	{
		return recvQueue.Take();
	}

	// pseudo-destructor
	public void Destroy()
	{
		netThread.Abort();
		NetMQConfig.Cleanup(false);
		GD.Print("EVI Connection completely shut down.");
	}

	// Worker Function for Network Thread
	void WorkNetThread()
	{
		GD.Print("Worker Thread Started");

		GD.Print("Opened connection to EVI at address: " + EVIAdress);
		bool running = true;

		while (running)
		{
			try
			{
				if (NewFrameAvailable)
				{
					dealerSock.SendFrame(NextFrameUpdate.ToByteArray());
						NewFrameAvailable = false;
				
					 	List<byte[]> multipartResult = new List<byte[]>(); // = dealerSock.ReceiveMultipartBytes();
					 	if (dealerSock.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(300000), ref multipartResult))
					 	{
						 FrameWasUpdated = true;
						 //GD.Print("Got message");
						 foreach (var resultFrame in multipartResult)
						 {
							 Asmp.Message msgReply = Asmp.Message.Parser.ParseFrom(resultFrame);
							 //GD.Print("Process message");
							 processMessage(msgReply);
						 }
						 EmitSignal("newUpdateArrived");
						
					 	}
				}
			}
			catch (ThreadAbortException e)
			{
				running = false;
				dealerSock.Close();

				GD.Print("netThread aborted due to " + e.ToString());
			}
		}

	}
	// Process message extracted from EVI
	private void processMessage(Asmp.Message msgReply)
		{
		if (msgReply.MessageOneofCase == Asmp.Message.MessageOneofOneofCase.Vehicle)
		{
				if (isDoorUpdate(msgReply))
				{
					doorStates = ExtractDoorUpdate(msgReply.Vehicle);
				}

				foreach (VehicleData vehicle in ExtractVehicleUpdate(msgReply.Vehicle).Values)
				{
				switch (vehicle.stateOfExistence)
				{
					case Command.CommandOneofOneofCase.RegisterVehicleCommand:
						registerCommands[vehicle.vehicleId] = (vehicle);
						break;
					case Command.CommandOneofOneofCase.UpdateVehicleCommand:
						updateVehicleCommands[vehicle.vehicleId] = vehicle;
						break;
					case Command.CommandOneofOneofCase.UnregisterVehicleCommand:
						unregisterCommands[vehicle.vehicleId] = (vehicle);
						break;
					default:
						otherVehicleCommands[vehicle.vehicleId] = vehicle;
						break;
				}
				}
		}
		else
		{
				recvQueue.Add(msgReply);
		}
		}

	private Dictionary<uint, VehicleData> ExtractVehicleUpdate(Asmp.Vehicle.Message vehicleMsg)
	{
		var result = new Dictionary<uint, VehicleData>();
		foreach (var cmd in vehicleMsg.Commands)
		{
			if (cmd.CommandOneofCase == Asmp.Vehicle.Command.CommandOneofOneofCase.UpdateVehicleCommand)
			{
				var vcmd = cmd.UpdateVehicleCommand;
				result[vcmd.VehicleId] = ExtractDataFromMsgState(vcmd.State, vcmd.VehicleId, vcmd.IsEgoVehicle, cmd.CommandOneofCase);
			}
			else if (cmd.CommandOneofCase == Asmp.Vehicle.Command.CommandOneofOneofCase.RegisterVehicleCommand)
			{
				var vcmd = cmd.RegisterVehicleCommand;
				result[vcmd.VehicleId] =
					ExtractDataFromMsgState(
						vcmd.State,
						vcmd.VehicleId,
						vcmd.IsEgoVehicle,
						cmd.CommandOneofCase,
						vcmd.VehType
					);
			}
			else if (cmd.CommandOneofCase == Asmp.Vehicle.Command.CommandOneofOneofCase.UnregisterVehicleCommand)
			{
				var vcmd = cmd.UnregisterVehicleCommand;
				result[vcmd.VehicleId] = new VehicleData(
					vcmd.VehicleId,
					0,
					0,
					0,
					0,
					null,
					null,
					0,
					0,
					cmd.CommandOneofCase,
					false,
					false,
					false,
					false,
					false,
					false,
					cmd.UnregisterVehicleCommand.IsEgoVehicle
				);
			}
		}

		return result;
	}
	// Extract car data
	private VehicleData ExtractDataFromMsgState(Asmp.Vehicle.VehicleState state, uint vehicleId, bool isEgoVehicle,
		Command.CommandOneofOneofCase stateOfExistence,
		RegisterVehicleCommand.Types.VehicleType vehicleType = RegisterVehicleCommand.Types.VehicleType.PassengerCar)
	{
		var brakeLightOn = state.Signals.Contains(VehicleState.Types.VehicleSignal.Breaklight);
		var turnSignalLeftOn = state.Signals.Contains(VehicleState.Types.VehicleSignal.BlinkerLeft);
		var turnSignalRightOn = state.Signals.Contains(VehicleState.Types.VehicleSignal.BlinkerRight);
		var emergencyLightsOn = state.Signals.Contains(VehicleState.Types.VehicleSignal.BlinkerEmergency);
		// Signals regarding the doors may not be changed by the signals generated from sumo because they will always close the doors.
		// Doors are controlled by updates sent from veins. vehicle updates which are sent from veins are processed in ExtractDoorUpdate function.
		var doorOpenLeft = false;
		var doorOpenRight = false;

		return new VehicleData(
			vehicleId,
			state.Position.Px - xOffset,
			state.Position.Py - yOffset,
			state.Position.RoadId,
			state.Position.LaneId,
			state.Position.EdgeId,
			null,
			state.SpeedMps,
			state.Position.Angle,
			stateOfExistence,
			brakeLightOn,
			turnSignalLeftOn,
			turnSignalRightOn,
			emergencyLightsOn,
			doorOpenLeft,
			doorOpenRight,
			isEgoVehicle,
			vehicleType
			);
	}
	// Implemented for Unity, not used in Godot
	private bool isDoorUpdate(Asmp.Message msgReply)
	{
		int firstVehicleUpdate = -1; // index of first vehicle update
		for (int i = 0; i < msgReply.Vehicle.Commands.Count; ++i)
		{
			if (msgReply.Vehicle.Commands[i].CommandOneofCase ==
				Asmp.Vehicle.Command.CommandOneofOneofCase.UpdateVehicleCommand)
			{
				firstVehicleUpdate = i;
			}
		}

		if (firstVehicleUpdate != -1)
		{
			var cmd = msgReply.Vehicle.Commands[firstVehicleUpdate];
			var vcmd = cmd.UpdateVehicleCommand;
			if (vcmd.State.Position == null)
			{
				// only door updates
				return true;
			}
			else
			{
				// normal position updates
				return false;
			}
		}
		else
		{
			return false;
		}
	}
	// Implemented for Unity, not used in Godot
	private Dictionary<uint, VehicleData> ExtractDoorUpdate(Asmp.Vehicle.Message vehicleMsg)
	{
		var result = new Dictionary<uint, VehicleData>();
		int vehicleCommandCount = vehicleMsg.Commands.Count;
		for (int i = 0; i < vehicleCommandCount; ++i)
		{
			// DoorUpdates only contain UpdateVehicleCommand commands. There is no need to check for them.
			var vcmd = vehicleMsg.Commands[i].UpdateVehicleCommand;
			result[vcmd.VehicleId] =
				ExtractDoorFlagsFromMsgState(vcmd.State, vcmd.VehicleId, vcmd.IsEgoVehicle, vehicleMsg.Commands[i].CommandOneofCase);
		}

		return result;
	}
	// Implemented for Unity, not used in Godot
	private VehicleData ExtractDoorFlagsFromMsgState(Asmp.Vehicle.VehicleState state, uint vehicleId, bool isEgoVehicle,
		Command.CommandOneofOneofCase stateOfExistence)
	{
		return new VehicleData(
			vehicleId,
			0,
			0,
			0,
			0,
			null,
			null,
			0,
			0,
			stateOfExistence,
			false,
			false,
			false,
			false,
			state.Signals.Contains(VehicleState.Types.VehicleSignal.DoorOpenLeft),
			state.Signals.Contains(VehicleState.Types.VehicleSignal.DoorOpenRight),
			isEgoVehicle
		);
	}
	public IDisposable Subscribe(IObserver<Dictionary<uint, VehicleData>> observer)
		{
		   	// Check whether observer is already registered. If not, add it
			if (!observers.Contains(observer))
			{
		 	   	observers.Add(observer);
			}
	  	  	return null;
	
		}

}
