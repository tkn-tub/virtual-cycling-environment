using Godot;
using System;
using System.Linq;
using System.Collections.Generic;
using Asmp.Vehicle;
using extrapolation;

public class VehicleManager : Spatial
{

	private uint _egoVehicleHashId;
	private bool _egoVehicleRegistered;
	private Vector3 _sumoOffset;
	// private SimpleVehicleController _egoVehicle;
	private BicycleInterfaceController _egoInterfaceVehicle;
	private SimpleVehicleController _egoSimpleVehicle;
	public Dictionary<uint, ForeignVehicleController> _vehicles3D;
	private List<Color> _eviCarColors;
	private Random _random;
	private string _vehicleType;
	public void Init(uint egoVehicleHashId, string vehicleType)
	{
		_egoVehicleHashId = egoVehicleHashId;
		_vehicleType = vehicleType;

		// CHange between different bicycle controllers
		if(_vehicleType == "BICYCLE_INTERFACE"){
			_egoInterfaceVehicle = (BicycleInterfaceController)GameStatics.GameInstance.PlayerVehicle;
		}else{
			_egoSimpleVehicle = (SimpleVehicleController)GameStatics.GameInstance.PlayerVehicle;
		}
		
		_sumoOffset = GameStatics.SumoOffset;
		_vehicles3D = new Dictionary<uint, ForeignVehicleController>();

		// Init Colors
		_random = new Random();
		_eviCarColors = new List<Color>();
		for (var i = 0; i <= 16; i++)
		{
			var c = new Color(i / 16f, i / 16f, i / 16f);
			_eviCarColors.Add(c);
		}

	}
	private Vector3 GetSpeedVector(double pYawRate, double pSpeed)
	{
		//MonoBehaviour.print ("YawRate: " + pYawRate + " Speed: " + pSpeed);
		double yawRateRad = Math.PI * pYawRate / 180;
		float speedX = (float)(Math.Cos(yawRateRad) * pSpeed);
		float speedZ = (float)(Math.Sin(yawRateRad) * pSpeed);

		if (yawRateRad >= 0 && yawRateRad <= Math.PI)
		{
			speedZ = -1 * Math.Abs(speedZ);
		}
		else
		{
			speedZ = Math.Abs(speedZ);
		}

		if (yawRateRad >= (Math.PI / 2) && yawRateRad <= ((3 * Math.PI) / 2))
		{
			speedX = -1 * Math.Abs(speedX);
		}
		else
		{
			speedX = Math.Abs(speedX);
		}

		return new Vector3(
			speedX,
			0.0f,
			speedZ
		);
	}


	public void ConvergeFellowVehicles(Dictionary<uint, VehicleData> vehicleData, uint pStepsWithoutVehicleUpdate)
	{
		foreach (var veh in vehicleData.Values.ToList().Where(veh => veh.vehicleId != _egoVehicleHashId))
		{
			var vehicle = _vehicles3D[veh.vehicleId];
			if (IsInstanceValid(vehicle) == false)
					continue;
			vehicle.targetTranslation = new Vector3((float)-veh.xCoord, 0f, (float)veh.yCoord);
			vehicle.targetRotation = new Quat(new Vector3(0f, Mathf.Deg2Rad((float)-veh.yawRate - 90.0f), 0f)).Normalized();
			vehicle.vehicleSpeed = veh.speed; 
			vehicle.updateSignalsBool(
					
				veh.turnSignalLeftOn,
				veh.turnSignalRightOn

			);

			vehicle.updateStopLight(
				veh.brakeLightOn
			);
			
		}
	}
	
	public void ExtrapolateFellowVehicles(uint pStepsWithoutVehicleUpdate, double timePassed)
	{
		//somehow need to handl
		foreach (var veh in _vehicles3D.Values.ToList().Where(veh => veh.vehicleId != _egoVehicleHashId))
		{
			if (veh.isEgoVehicle == true)
			{
			   //UnityEngine.Debug.Log("egoVehcile");
			   if(Extrapolation.CloseToIntersection(veh.targetTranslation, veh.vehicleSpeed, veh.edgeId, veh.laneId, _sumoOffset.x, _sumoOffset.z))
				{
					ExtrapolateStopping(veh);
				}
				else
				{
					ExtrapolateOneStep(veh, timePassed);
					//extrapolateOneStepOnStreet(veh, veh.lane);
				}
				

			}
			else
			{
				//extrapolate
				bool isClose = Extrapolation.CloseToIntersection(veh.targetTranslation, veh.vehicleSpeed, veh.edgeId, veh.laneId, _sumoOffset.x, _sumoOffset.z);
				
				// check if close to intersection
				if (isClose)
				{
					//check for turning lights 
					//0 no lights, 1 left, 2 right
					int turningLight = Extrapolation.TurningLightValue(veh);
					// Do motion accordinly
					if (turningLight == 1) {
						ExtrapolateStopping(veh);
					}
					else if (turningLight == 2) {
						ExtrapolateStopping(veh);
					}
					else {
						ExtrapolateOneStep(veh, timePassed);
						//extrapolateOneStepOnStreet(veh, veh.lane);
						//extrapolateStopping(veh);
					}
				}
				else
				{
					ExtrapolateOneStepOnStreet(veh, veh.lane, timePassed);
				}
				
			}
		}
		
	}

	private void ExtrapolateOneStep(ForeignVehicleController veh, double timePassed)
	{
		//make car drive straight ahead with same speed
		ForeignVehicleController updated = Extrapolation.KeepSpeedAndDirection(veh, timePassed);
		// update value in fellow Vehicles
		_vehicles3D[veh.vehicleId].targetTranslation = updated.targetTranslation;
		_vehicles3D[veh.vehicleId].targetRotation = updated.targetRotation;
		_vehicles3D[veh.vehicleId].vehicleSpeed = updated.vehicleSpeed;
	}

	private void ExtrapolateOneStepOnStreet(ForeignVehicleController veh, NetFileLane lane, double timePassed)
	{
		//make car drive straight ahead with same speed, but stay on street
		ForeignVehicleController updated = Extrapolation.KeepSpeedAndStayonStreet(timePassed, veh, lane, this._sumoOffset.x, this._sumoOffset.z);
		// update value in fellow Vehicles
		_vehicles3D[veh.vehicleId].targetTranslation = updated.targetTranslation;
		_vehicles3D[veh.vehicleId].targetRotation = updated.targetRotation;
		_vehicles3D[veh.vehicleId].vehicleSpeed = updated.vehicleSpeed;
	}

	private void ExtrapolateStopping(ForeignVehicleController veh)
	{
		ForeignVehicleController updated = Extrapolation.StopAtIntersection(veh);
		// update value in fellow Vehicles
		_vehicles3D[veh.vehicleId].targetTranslation = updated.targetTranslation;
		_vehicles3D[veh.vehicleId].targetRotation = updated.targetRotation;
		_vehicles3D[veh.vehicleId].vehicleSpeed = updated.vehicleSpeed;
	}
	
	
	public void UpdateFellowVehicles(Dictionary<uint, VehicleData> vehicleData)
	{
		foreach (var veh in vehicleData.Values.ToList().Where(veh => veh.vehicleId != _egoVehicleHashId))
		{
			if (veh.stateOfExistence == Command.CommandOneofOneofCase.UnregisterVehicleCommand &&
				_vehicles3D.ContainsKey(veh.vehicleId))
			{
				// Remove 3D Vehicle
				GD.Print($"Removing vehicle {veh.vehicleId}");
				_vehicles3D[veh.vehicleId].QueueFree();
				// _vehicles3D.Remove(veh.vehicleId); Uncommenting this breaks the removal of vehicles from Godot
				continue;
			}

			// Create new 3D Vehicle
			if (!_vehicles3D.ContainsKey(veh.vehicleId))
			{
				ForeignVehicleController vehicle;
				PackedScene vehicleScene;
				if (veh.vehicleType == RegisterVehicleCommand.Types.VehicleType.Bicycle)
				{
					vehicleScene = ResourceLoader.Load<PackedScene>("res://Vehicles/Bicycle/ForeignBicycle.tscn");
					vehicle = vehicleScene.Instance<ForeignVehicleController>();
					vehicle.vehicleId = veh.vehicleId;
				}
				else
				{
					vehicleScene = ResourceLoader.Load<PackedScene>("res://Vehicles/DefaultCar/ForeignCar.tscn");
					vehicle = vehicleScene.Instance<ForeignVehicleController>();
					vehicle.signalLeft = vehicle.GetNode<OmniLight>("Car/TurnLeftSignal");
					vehicle.signalRight = vehicle.GetNode<OmniLight>("Car/TurnRightSignal");
					vehicle.signalStop = vehicle.GetNode<OmniLight>("Car/StopSignal");
					vehicle.signalLeft.Visible = false;
					vehicle.signalRight.Visible = false;
					vehicle.signalStop.Visible = false;
					vehicle.vehicleId = veh.vehicleId;
				}
				vehicle.lane = veh.lane;
				// vehicle = vehicleScene.Instance<ForeignVehicleController>();
				vehicle.ChangeColor(_eviCarColors[_random.Next(_eviCarColors.Count)]);
				vehicle.Translation = new Vector3((float)-veh.xCoord, 0f, (float)veh.yCoord);
				vehicle.Rotation = new Vector3(0f, Mathf.Deg2Rad((float)-veh.yawRate - 90.0f), 0f);
				vehicle.Name = "Vehicle: " + veh.vehicleId.ToString();
				
				AddChild(vehicle);
				_vehicles3D.Add(veh.vehicleId, vehicle);
			}
			// Vehicle Exists, update position and signals
			else
			{      
				var vehicle = _vehicles3D[veh.vehicleId];
				if (IsInstanceValid(vehicle) == false)
					continue;
				vehicle.targetTranslation = new Vector3((float)-veh.xCoord, 0f, (float)veh.yCoord);
				vehicle.targetRotation = new Quat(new Vector3(0f, Mathf.Deg2Rad((float)-veh.yawRate - 90.0f), 0f)).Normalized();
				vehicle.vehicleSpeed = veh.speed; 
				vehicle.lane = veh.lane;
				
				vehicle.updateSignalsBool(
					
					veh.turnSignalLeftOn,
					veh.turnSignalRightOn

				);

				vehicle.updateStopLight(
					veh.brakeLightOn
				);

				
				

			}
		}
	}

	private Asmp.Vehicle.Command MakeRegisterCommand(VehicleData vData)
	{

		var cmd = new Asmp.Vehicle.Command
		{
			RegisterVehicleCommand = new Asmp.Vehicle.RegisterVehicleCommand
			{
				State = vData.toVehicleStateMsg(),
				VehicleId = vData.vehicleId,
				IsEgoVehicle = true
			}
		};

		LevelAndConnectionSettings settings = GetNode<LevelAndConnectionSettings>("/root/World/VCESettings/LevelAndConnectionSettings");
		string vehicleType = settings.GetSelectedVehicleType();

		GD.Print($"Registering ego vehicle with hash id {cmd.RegisterVehicleCommand.VehicleId}");

		//TODO: Add other vehicle types; make minimap an option?
		cmd.RegisterVehicleCommand.VehType = vehicleType switch
		{
			"CAR" => RegisterVehicleCommand.Types.VehicleType.PassengerCar,
			"BICYCLE" => RegisterVehicleCommand.Types.VehicleType.Bicycle,
			"BICYCLE_INTERFACE" => RegisterVehicleCommand.Types.VehicleType.Bicycle,
			"BICYCLE_WITH_MINIMAP" => RegisterVehicleCommand.Types.VehicleType.Bicycle,
			_ => throw new ArgumentException(
				$"Vehicle type {vehicleType} is not defined for "
				+ "MakeRegisterCommand()."
			)
		};

		return cmd;
	}

	private static Asmp.Vehicle.Command MakeUpdateCommand(VehicleData vData)
	{
		var cmd = new Asmp.Vehicle.Command();
		cmd.UpdateVehicleCommand = new Asmp.Vehicle.UpdateVehicleCommand();
		cmd.UpdateVehicleCommand.State = vData.toVehicleStateMsg();
		cmd.UpdateVehicleCommand.VehicleId = vData.vehicleId;
		return cmd;
	}

	uint _messageId = 0;
	public Asmp.Message SyncEgoVehicle()
	{
		VehicleData vData = GetEgoVehicleState();
		Asmp.Message msg = new Asmp.Message();
		msg.Id = _messageId++;
		msg.Vehicle = new Asmp.Vehicle.Message();
		//msg.Vehicle.TimeS = (stepLengthMilliseconds * vehicleUpdateStep) / 1000.0;
		if (_egoVehicleRegistered)
		{
			msg.Vehicle.Commands.Add(MakeUpdateCommand(vData));
		}
		else
		{
			msg.Vehicle.Commands.Add(MakeRegisterCommand(vData));
			_egoVehicleRegistered = true;
		}

		return msg;
	}
	private VehicleData GetEgoVehicleState()
	{
		// Get the current position of the ego vehicle in Godot, flip the X coordinate to match the Sumo coordinate system
		
		if (_vehicleType == "BICYCLE_INTERFACE")
		{
			return new VehicleData(
				_egoVehicleHashId,
				-(_egoInterfaceVehicle.Translation.x + _sumoOffset.x),
				_egoInterfaceVehicle.Translation.z + _sumoOffset.z,
				0,
				0,
				null,
				null,
				_egoInterfaceVehicle.GetSpeed(),
				-_egoInterfaceVehicle.RotationDegrees.y - 90.0f,
				Command.CommandOneofOneofCase.UpdateVehicleCommand,
				false,
				false,
				false,
				false,
				false,
				false,
				false);
		}
		else
		{
			return new VehicleData(
			_egoVehicleHashId,
			-(_egoSimpleVehicle.Translation.x + _sumoOffset.x),
			_egoSimpleVehicle.Translation.z + _sumoOffset.z,
			0,
			0,
			null,
			null,
			_egoSimpleVehicle.GetSpeed(),
			-_egoSimpleVehicle.RotationDegrees.y - 90.0f,
			Command.CommandOneofOneofCase.UpdateVehicleCommand,
			false,
			false,
			false,
			false,
			false,
			false,
			false);
		}
	}
}
