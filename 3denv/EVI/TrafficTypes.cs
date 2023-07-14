using Asmp.Vehicle;
using extrapolation;

public class VehicleData
{
	public uint vehicleId;
	public double xCoord;
	public double yCoord;
	public uint roadId,
		laneId;
	public string edgeId;
	public NetFileLane lane;
	public double speed;
	public double angleDeg; // 0 is North
	public RegisterVehicleCommand.Types.VehicleType vehicleType;

	public bool brakeLightOn,
		turnSignalLeftOn,
		turnSignalRightOn,
		emergencyLightsOn,
		doorOpenLeft,
		doorOpenRight,
		isEgoVehicle;

	public Command.CommandOneofOneofCase stateOfExistence = Command.CommandOneofOneofCase.RegisterVehicleCommand;

	public VehicleData(uint pVehicleId, double pXCoord, double pYCoord, uint pRoadId, uint pLaneId, string pEdgeId, NetFileLane pLane, double pSpeed, double pAngleDeg,
		Command.CommandOneofOneofCase pStateOfExistence, bool pBrakeLightOn, bool pTurnSignalLeftOn,
		bool pTurnSignalRightOn, bool pEmergencyLightsOn, bool pDoorOpenLeft, bool pDoorOpenRight, bool pisEgoVehicle,
		RegisterVehicleCommand.Types.VehicleType pVehicleType = RegisterVehicleCommand.Types.VehicleType.PassengerCar)    {
		vehicleId = pVehicleId;
		xCoord = pXCoord;
		yCoord = pYCoord;
		roadId = pRoadId;
		laneId = pLaneId;
		edgeId = pEdgeId;
		lane = pLane;
		speed = pSpeed;
		angleDeg = pAngleDeg;
		stateOfExistence = pStateOfExistence;
		brakeLightOn = pBrakeLightOn;
		turnSignalLeftOn = pTurnSignalLeftOn;
		turnSignalRightOn = pTurnSignalRightOn;
		emergencyLightsOn = pEmergencyLightsOn;
		doorOpenLeft = pDoorOpenLeft;
		doorOpenRight = pDoorOpenRight;
		vehicleType = pVehicleType;
		isEgoVehicle = pisEgoVehicle;
	}
	/*
	public VehicleData(RegisterVehicleCommand registerVehicleCommand)
	{
		vehicleId = pVehicleId;
		xCoord = pXCoord;
		yCoord = pYCoord;
		roadId = pRoadId;
		speed = pSpeed;
		angleDeg = pAngleDeg;
		stateOfExistence = pStateOfExistence;
		brakeLightOn = pBrakeLightOn;
		turnSignalLeftOn = pTurnSignalLeftOn;
		turnSignalRightOn = pTurnSignalRightOn;
		emergencyLightsOn = pEmergencyLightsOn;
		doorOpenLeft = pDoorOpenLeft;
		doorOpenRight = pDoorOpenRight;
		vehicleType = pVehicleType;
	}
	public VehicleData(UpdateVehicleCommand updateVehicleCommand)
	{
		vehicleId = pVehicleId;
		xCoord = pXCoord;
		yCoord = pYCoord;
		roadId = pRoadId;
		speed = pSpeed;
		angleDeg = pAngleDeg;
		stateOfExistence = pStateOfExistence;
		brakeLightOn = pBrakeLightOn;
		turnSignalLeftOn = pTurnSignalLeftOn;
		turnSignalRightOn = pTurnSignalRightOn;
		emergencyLightsOn = pEmergencyLightsOn;
		doorOpenLeft = pDoorOpenLeft;
		doorOpenRight = pDoorOpenRight;
		vehicleType = pVehicleType;
	}
	public VehicleData(UnregisterVehicleCommand unregisterVehicleCommand)
	{
		vehicleId = pVehicleId;
		xCoord = pXCoord;
		yCoord = pYCoord;
		roadId = pRoadId;
		speed = pSpeed;
		angleDeg = pAngleDeg;
		stateOfExistence = pStateOfExistence;
		brakeLightOn = pBrakeLightOn;
		turnSignalLeftOn = pTurnSignalLeftOn;
		turnSignalRightOn = pTurnSignalRightOn;
		emergencyLightsOn = pEmergencyLightsOn;
		doorOpenLeft = pDoorOpenLeft;
		doorOpenRight = pDoorOpenRight;
		vehicleType = pVehicleType;
	}*/

	public Asmp.Vehicle.VehicleState toVehicleStateMsg()
	{
		var msg = new Asmp.Vehicle.VehicleState();
		msg.SpeedMps = speed;
		msg.Position = new Asmp.Vehicle.VehiclePosition();
		msg.Position.Px = xCoord;
		msg.Position.Py = yCoord;
		msg.Position.RoadId = roadId;
		msg.Position.LaneId = laneId;
		msg.Position.Angle = angleDeg;
		return msg;
	}
}

public class TrafficlightData
{
	public uint tlId;
	public string signals;

	public TrafficlightData(uint pTlId, string pSignals)
	{
		tlId = pTlId;
		signals = pSignals;
	}
}

public class VisualizationData
{
	public uint entityId;

	public VisualizationData(uint pEntityId)
	{
		entityId = pEntityId;
	}
}

public class GenericWarning : VisualizationData
{
	public double intensity;
	public string description;

	public GenericWarning(uint pEntityId, double pIntensity, string pDescription) : base(pEntityId)
	{
		intensity = pIntensity;
		description = pDescription;
	}
}

public class ReceivedWirelessMessage : VisualizationData
{
	public uint senderId;
	public double arrivalTime;
	public double xCoord;
	public double yCoord;
	public double angle;
	public double lon;
	public double lat;

	public ReceivedWirelessMessage(uint pEntityId, uint pSenderId, double pArrivalTime, double pXCoord, double pYCoord,
		double pAngle, double pLon, double pLat) : base(pEntityId)
	{
		senderId = pSenderId;
		arrivalTime = pArrivalTime;
		xCoord = pXCoord;
		yCoord = pYCoord;
		angle = pAngle;
		lon = pLon;
		lat = pLat;
	}
}

public class BicycleFeedback
{
	public uint entityId;
	public uint dangers;
	public string vibrations;
	public string pattern;

	public BicycleFeedback(uint pEntityId, uint pDangers, string pVibrations, string pPattern)
	{
		entityId = pEntityId;
		dangers = pDangers;
		vibrations = pVibrations;
		pattern = pPattern;
	}
}


