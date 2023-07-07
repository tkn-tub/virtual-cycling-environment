

using Godot;
using System.Collections.Generic;
using System.Diagnostics;
using System.Xml.Serialization;
using System.IO;
using extrapolation;




public partial class EviConnector : Spatial//, IObserver<Dictionary<uint, VehicleData>>
{
	private string _egoVehicleHashStr;
	private uint _egoVehicleHashId;
	private string vehicleType;

	public string egoVehicleName = "ego-vehicle";
	public string EVIAddress;
	public int EVIPort;
	
	
	double time;
	public ThreadedRequestWorker netWorker;

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

		//TODO: read in file from Menue
		Extrapolation.ParseXmlFiles("../scenarios/3denv-networks/paderborn-north-toj.net.xml");
		
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
		//bool gotVehicleCommands = false;

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
			
			time = 0.0;
			gotNewUpdates = false;
			stepsWithoutVehicleUpdate = 0;
			lastUpdate = time;
//
//			if ( newVehicleStates.Count > 0)
//				{
//					gotVehicleCommands = true;
//					waitSteps = waitSteps - 1;
//
//					if (waitSteps<=0)
//					{
//
//						if (extrapolated)
//						{
//							// convergence
//							extrapolated = false;
//							_vehicleManager.ConvergeFellowVehicles(newVehicleStates, stepsWithoutVehicleUpdate);
//						}
//						else
//						{
							_vehicleManager.UpdateFellowVehicles(newVehicleStates);
//							waitSteps = 0;
//
//
//						}
//
//						//fellowVehicles = newVehicleStates; // override for next step
//						// clear because otherwise the interpolation is never called because the list is never empty and gotVehicleCommands is always set true;
//
//					}
//					else
//					{
//
//						_vehicleManager.ExtrapolateFellowVehicles(stepsWithoutVehicleUpdate, time);
//					}
//					netWorker.updateVehicleCommands.Clear();
//				}
//
//
//
//		}
//
//		if (!gotVehicleCommands && _vehicleManager._vehicles3D.Count > 0)
//		{
//			extrapolated = true;
//			_vehicleManager.ExtrapolateFellowVehicles(stepsWithoutVehicleUpdate, time);
//			//interpolateFellowVehicles(fellowVehicles, stepsWithoutVehicleUpdate);
//			if (time - (lastUpdate + stepLengthMilliseconds * waitSteps) >= 0)
//			{
//				waitSteps++;
//			}
//
		}
		// Get new update from EVI
		while (netWorker.HasResults())
		{
			var msgReply = netWorker.Recv();

			switch (msgReply.MessageOneofCase)
			{
				case Asmp.Message.MessageOneofOneofCase.Trafficlight:
					{
						//GameStatics.GameInstance.TrafficLightsManager.ExtractTrafficLightUpdate(msgReply.Trafficlight);
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



	




}

