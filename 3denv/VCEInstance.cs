using Godot;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using static Godot.Performance;
using CsvHelper;


public class VCEInstance : Spatial
{
	private Control VCESettings;

	public KinematicBody PlayerVehicle { get; private set; }
	public Transform PlayerStartPoint { get; private set; } = Transform.Identity;
	public NetworkGenerator SUMONetworkGenerator { get; private set; }

	public TrafficLightsManager TrafficLightsManager { get; private set; }

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		GameStatics.SetGameInstance(this);
		VCESettings = GetNode<Control>("VCESettings");
		SUMONetworkGenerator = GetNode<NetworkGenerator>("NetworkGenerator");

		TrafficLightsManager = new TrafficLightsManager();

		// TODO: already use the settings from VCESettings here
		//  (it should return either the defaults or cmdline values)
		var settings = GetNode<LevelAndConnectionSettings>("/root/World/VCESettings/LevelAndConnectionSettings");
		// Load default network when starting the game
		SUMONetworkGenerator.LoadNetwork(
			settings.GetSelectedSumoNetFile(),
			settings.GetSeed(),
			settings.GetStreetLightsChecked()
		);
		
		ChangePlayerVehicle(
			GameStatics.VehicleTypes[settings.GetSelectedVehicleType()].Item2
			// Item2 is the resource path
		);

		SetMenuVisibility(!settings.GetSkipMenu());
		if (settings.GetConnectToEVIOnLaunch())
		{
			ConnectToEVI(
				settings.GetEgoVehicleName(),
				settings.GetEVIAddress(),
				settings.GetEVIPort(),
				settings.GetSelectedVehicleType()
			);
		}
	}

	public override void _Input(InputEvent @event)
	{
		base._Input(@event);
		if (@event.IsActionPressed("ToogleUI"))
		{
			ToggleMenu();
		}
	}

	public void ChangePlayerVehicle(string VehiclePath)
	{
		if (PlayerVehicle is not null)
			PlayerVehicle.QueueFree();

		PackedScene vehicleScene = ResourceLoader.Load<PackedScene>(VehiclePath);
		PlayerVehicle = vehicleScene.Instance<KinematicBody>();
		PlayerVehicle.Transform = PlayerStartPoint;
		AddChild(PlayerVehicle);
	}

	public void UpdatePlayerStartPosition(Transform newPosition)
	{
		PlayerStartPoint = newPosition;
		if (PlayerVehicle is not null)
		{
			PlayerVehicle.Transform = newPosition;
		}
	}

	public void ConnectToEVI(string EgoVehicleName, string IP, int Port, string VehicleType)
	{
		PackedScene eviConnectorScene = ResourceLoader.Load<PackedScene>("res://EVI/EviConnector.tscn");
		EviConnector eviConnector = eviConnectorScene.Instance<EviConnector>();
		//init evi connector
		eviConnector.Init(IP, Port, EgoVehicleName, VehicleType);
		AddChild(eviConnector);

		// Create connection to speed and steering sensors for bicycle interface
		if (VehicleType == "BICYCLE_INTERFACE")
		{
			PackedScene networkListenerScene = ResourceLoader.Load<PackedScene>("res://Vehicles/Bicycle/InterfaceController/NetworkListener.tscn");
			NetworkListener networkListener = networkListenerScene.Instance<NetworkListener>();
			//init receive
			networkListener.Init();
			AddChild(networkListener);
		}
		
	}

	public void GenerateNetwork(string SumoNetFile, int Seed, bool GenerateStreetLights)
	{
		SUMONetworkGenerator.LoadNetwork(SumoNetFile, Seed, GenerateStreetLights);
	}

	public void ToggleMenu()
	{
		SetMenuVisibility(!VCESettings.Visible);
	}

	public void SetMenuVisibility(bool visible)
	{
		VCESettings.Visible = visible;
		Input.MouseMode = VCESettings.Visible ?
			Input.MouseModeEnum.Visible : Input.MouseModeEnum.Captured;
	}


	#region performance measurement functions

	private Timer perfromanceTimer;
	public bool TooglePerformanceMeasurement()
	{
		if (perfromanceTimer == null)
		{
			perfromanceTimer = new Timer();

			GD.Print("Performance Timer Started");
			perfromanceTimer.Connect("timeout", this, "LogFPS");
			AddChild(perfromanceTimer);
			perfromanceTimer.Start();
			return true;
		}
		else
		{
			if (perfromanceTimer.IsStopped())
			{
				GD.Print("Performance Timer Started");
				perfromanceTimer.Start();
				return true;
			}
			else
			{
				perfromanceTimer.Stop();
				GD.Print("Performance Timer Stopped");


				int averageFPS = 0, maxFPS = 0, minFPS = int.MaxValue, top95FPS;

				fpsList.Sort();
				top95FPS = fpsList[(int)(fpsList.Count * 0.05)];

				StringBuilder sb = new StringBuilder();

				for (int i = 0; i < fpsList.Count; i++)
				{
					int fps = fpsList[i];

					if (fps > maxFPS)
					{
						maxFPS = fps;
					}

					if (fps < minFPS)
					{
						minFPS = fps;
					}

					averageFPS += fps;


					sb.AppendLine(fps.ToString());
				}

				averageFPS /= fpsList.Count;

				string results = string.Format("FPS results Godot: \nTime: {4} \nAverage FPS: {0} \nMin FPS: {1} \nMax FPS: {2} \n95% of FPS over: {3}\n\n All measurements:\n----------------------------------\n",
					 averageFPS, minFPS, maxFPS, top95FPS, fpsList.Count);



				string date = DateTime.Now.ToShortTimeString().Replace(":", "-");
				string fileName = string.Format("GodotPerformanceLog-{0}.txt", date);
				GD.Print("Saving results to: " + fileName);
				System.IO.File.WriteAllText(fileName, results + sb.ToString());
				fpsList.Clear();


				fileName = string.Format("logs/GodotMonitorLog-{0}.csv", DateTime.Now.ToShortTimeString().Replace(":", "-"));

				var writer = new StreamWriter(fileName);
				var csv = new CsvWriter(writer, System.Globalization.CultureInfo.InvariantCulture);
				csv.WriteRecords(records);
				writer.Flush();
				return false;
			}
		}
	}

	List<int> fpsList = new List<int>();
	List<object> records = new List<object>();
	int time = 0;
	public void LogFPS()
	{
		fpsList.Add((int)GetMonitor(Monitor.TimeFps));

		var vm = GetNodeOrNull("EviConnector/VehicleManager");
		int vehicleCount = 0;
		if (vm != null)
		{
			vehicleCount = vm.GetChildCount();

		}

		records.Add(new { Time = time, TimeProcess = GetMonitor(Monitor.TimeProcess), FPS = GetMonitor(Monitor.TimeFps), PhysicsProcess = GetMonitor(Monitor.TimePhysicsProcess), ObjectCount = GetMonitor(Monitor.ObjectCount), NodeCount = GetMonitor(Monitor.ObjectNodeCount), VehicleCount = vehicleCount, RenderObjectsInFrame = GetMonitor(Monitor.RenderObjectsInFrame), DrawCalls = GetMonitor(Monitor.RenderDrawCallsInFrame), VerticesInFrame = GetMonitor(Monitor.RenderVerticesInFrame) });
		time++;
	}
	#endregion
}
