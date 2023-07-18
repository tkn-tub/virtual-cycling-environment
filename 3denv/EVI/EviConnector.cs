

using Godot;
using System.Collections.Generic;
using System.Diagnostics;
using System.Xml.Serialization;
using System.IO;
using System.Linq;
using Env3d.SumoImporter;
using Env3d.SumoImporter.NetFileComponents;

public partial class EviConnector : Spatial//, IObserver<Dictionary<uint, VehicleData>>
{
	private string _egoVehicleHashStr;
	private uint _egoVehicleHashId;
	private string vehicleType;

	public string egoVehicleName = "ego-vehicle";
	public string EVIAddress;
	public int EVIPort;
	private Vector3 _sumoOffset;
	
	
	double time;
	public ThreadedRequestWorker netWorker;
	public Dictionary<uint, VehicleData> fellowVehicles;

	// Stopwatches for exchanging regular updates
	private Stopwatch _vehicleUpdateTimer;
	private uint _vehicleUpdateStep = 0;
	public uint stepsWithoutVehicleUpdate = 0;
	public double stepLengthMilliseconds = 100; // TODO: change this for smoother vehicles!!!
	int msgs = 0;
	int frames = 0;

		public bool extrapolated = false;
		
		// for oberserver pattern
		bool gotNewUpdates = false;
		public static int waitSteps = 0;
		public double lastUpdate = 0;
	 
	private VehicleManager _vehicleManager;
	private VisualizationManager _visualizationManager;



	public void Init(string EVIAddress, int EVIPort, string egoVehicleName, string vehicleType)
	{
		this.EVIAddress = EVIAddress;
		this.EVIPort = EVIPort;
		this.egoVehicleName = egoVehicleName;
		this.vehicleType = vehicleType;
		GD.Print("Vehicle type: ", vehicleType);
	}

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		var settings = GetNode<LevelAndConnectionSettings>("/root/World/VCESettings/LevelAndConnectionSettings");
		Extrapolation.ParseXmlFiles(settings.GetSelectedSumoNetFile());
		
		// Start the network worker
		_egoVehicleHashStr = MD5Hasher.getMD5(egoVehicleName);
		_egoVehicleHashId = MD5Hasher.getMD5Uint(egoVehicleName);
		GD.Print($"Ego vehicle has hashed ID {_egoVehicleHashId}");
		Vector3 sumoOffset = GameStatics.SumoOffset;
		GD.Print($"Starting EVIConnector with address {EVIAddress}");
		netWorker = new ThreadedRequestWorker($"tcp://{EVIAddress}:{EVIPort}", -sumoOffset.x, sumoOffset.z);
		netWorker.Connect("newUpdateArrived", this, "NewUpdateArrived");
			
		// Start the vehicle manager
		_vehicleManager = ResourceLoader.Load<CSharpScript>("res://EVI/VehicleManager.cs").New() as VehicleManager;
		_vehicleManager.Name = "VehicleManager";
		_vehicleManager.Init(_egoVehicleHashId, this.vehicleType);
		AddChild(_vehicleManager);
		_sumoOffset = _vehicleManager._sumoOffset;
		//Extrapolation._sumoOffset = this._sumoOffset;
		
		fellowVehicles = new Dictionary<uint, VehicleData>();
		
		// Start the visualization manager (Veins interaction)
		_visualizationManager = ResourceLoader.Load<CSharpScript>("res://EVI/VisualizationManager.cs").New() as VisualizationManager;
		_visualizationManager.Name = "VisualizationManager";
		AddChild(_visualizationManager);


		netWorker.SaveNextFrame(_vehicleManager.SyncEgoVehicle());
		time = 0.0;
		_vehicleUpdateTimer = Stopwatch.StartNew();
	}

	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(float delta)
	{

		frames++;
		stepsWithoutVehicleUpdate++;
		time = time + delta;
		//frames++;
		//stepsWithoutVehicleUpdate++;

		if (netWorker.registerCommands is { Count: > 0 })
		{
			_vehicleManager.UpdateFellowVehicles(netWorker.registerCommands);
			netWorker.registerCommands.Clear();
		}
		
		if (netWorker.unregisterCommands is { Count: > 0 })
		{
			_vehicleManager.UpdateFellowVehicles(netWorker.unregisterCommands);
			netWorker.unregisterCommands.Clear();
		}

		Dictionary<uint, VehicleData> newVehicleStates = netWorker.updateVehicleCommands;
		//GD.Print("Evi Connector");
		if (gotNewUpdates)
		{
			gotNewUpdates = false;
			stepsWithoutVehicleUpdate = 0;
			lastUpdate = time;

			if ( newVehicleStates.Count > 0)
			{
				waitSteps = waitSteps - 1;

				if (waitSteps<=0)
				{
						if (extrapolated)
						{
							// convergence
							//GD.Print("COnverge");
							extrapolated = false;
							_vehicleManager.ConvergeFellowVehicles(newVehicleStates);
						}
						else
						{
							_vehicleManager.UpdateFellowVehicles(newVehicleStates);
							waitSteps = 0;
						}

						fellowVehicles = new Dictionary<uint, VehicleData>(newVehicleStates); // override for next step
				}
				else
				{
					//GD.Print("Extrapolate");
			 		extrapolateFellowVehicles(fellowVehicles,stepsWithoutVehicleUpdate, delta);
					
				}
				netWorker.updateVehicleCommands.Clear();
				time = 0.0;
			}
		}

		if (!gotNewUpdates && fellowVehicles.Count > 0)
		{
			extrapolated = true;

			extrapolateFellowVehicles(fellowVehicles,stepsWithoutVehicleUpdate, delta);
			
			if (time - (lastUpdate + stepLengthMilliseconds * waitSteps) >= 0)
			{
				waitSteps++;
			}

		}
		// Get new update from EVI
		while (netWorker.HasResults())
		{
			var msgReply = netWorker.Recv();

			switch (msgReply.MessageOneofCase)
			{
				case Asmp.Message.MessageOneofOneofCase.Trafficlight:
				{
					GameStatics.GameInstance.TrafficLightsManager.ExtractTrafficLightUpdate(msgReply.Trafficlight);
					break;
				}
				case Asmp.Message.MessageOneofOneofCase.Visualization:
				{
					_visualizationManager.ExtractVisualizationUpdate(msgReply.Visualization);
					break;
				}
				case Asmp.Message.MessageOneofOneofCase.Hapticsignals:
				{
					break;
				}
				case Asmp.Message.MessageOneofOneofCase.Session:
				{
					break;
				}
				// ignore None, Vehicle (processed above), Cloud
			}

			msgs++;
		}

		// Check if we need to send a player vehicle update to EVI
		if (_vehicleUpdateTimer.ElapsedMilliseconds > stepLengthMilliseconds * _vehicleUpdateStep)
		{
			msgs = 0;
			frames = 0;
			_vehicleUpdateStep += 1;
			netWorker.SaveNextFrame(_vehicleManager.SyncEgoVehicle());
		}
	}

	private void NewUpdateArrived(){
		gotNewUpdates=true;
	}

	private void extrapolateFellowVehicles(Dictionary<uint, VehicleData> vehicleData, uint pStepsWithoutVehicleUpdate, double time)
	{
		foreach (var veh in vehicleData.Values.ToList())
		{
			if (veh.isEgoVehicle == true)
			{
			   if(Extrapolation.CloseToIntersection(veh, veh.edgeId, veh.laneId, _sumoOffset.x, _sumoOffset.z))
				{
					extrapolateStopping(veh);
				}
				else
				{
					extrapolateOneStep(veh,time);
					//extrapolateOneStepOnStreet(veh, veh.lane);
				}
			}
			else
			{
				//extrapolate
				bool isClose = Extrapolation.CloseToIntersection(veh, veh.edgeId, veh.laneId, _sumoOffset.x, _sumoOffset.z);
				
				// check if close to intersection
				if (isClose)
				{
					//check for turning lights 
					//0 no lights, 1 left, 2 right
					int turningLight = Extrapolation.TurningLightValue(veh);
					// Do motion accordinly
					if (turningLight == 1) {
						extrapolateStopping(veh);
					}
					else if (turningLight == 2) {
						extrapolateStopping(veh);
					}
					else {
						//extrapolateOneStep(veh,time);
						//extrapolateOneStepOnStreet(veh, veh.lane);
						extrapolateStopping(veh);
					}
				}
				else
				{
					extrapolateOneStepOnStreet(veh, veh.lane, time);
					//extrapolateOneStep(veh,time);
				}
			}
		}
		_vehicleManager.UpdateFellowVehicles(fellowVehicles);	
	}

	private void extrapolateOneStep(VehicleData veh, double time)
	{
		//make car drive straight ahead with same speed
		VehicleData updated = Extrapolation.KeepSpeedAndDirection(
			veh,
			time,
			_sumoOffset.x,
			_sumoOffset.y
		);
		// update value in fellow Vehicles
		fellowVehicles[veh.vehicleId] = updated;
	}

	private void extrapolateOneStepOnStreet(VehicleData veh, NetFileLane lane, double time)
	{
		
		VehicleData updated = Extrapolation.KeepSpeedAndStayonStreet(
			time,
			veh,
			lane,
			_sumoOffset.x,
			_sumoOffset.y
		);
		// update value in fellow Vehicles
		fellowVehicles[veh.vehicleId] = updated;
	}

	private void extrapolateStopping(VehicleData veh)
	{
		VehicleData updated = Extrapolation.StopAtIntersection(veh);
		// update value in fellow Vehicles
		fellowVehicles[veh.vehicleId] = updated;
	}
}
