using Godot;
using System;
using System.Globalization;
using System.Collections.Generic;


/// <summary>
/// Class which holds a collection of static variables and constants
/// </summary>
public static class GameStatics
{
	public const string DynamicBuildingtPath = @"Environment/Buildings/DynamicBuilding.tscn";
	public const string TrafficLightPath = @"Environment/TrafficLight/TrafficLight.tscn";
	public const string TrafficLightPanelPath = @"Environment/TrafficLight/TrafficLightPanel.tscn";
	public const string TrafficLightPoleExtendPath = @"Environment/TrafficLight/Mesh/TrafficLight_Extend.mesh";

	/// <summary>
	/// Define VehicleTypes
	/// Index: Used for the OptionButton in the UI.
	/// Keys: Used for the command line interface.
	/// Values: Tuples
	///   First item: Short description (again used for OptionButton)
	///	  Second item: Resource path
	/// </summary>
	public static SortedList<String, Tuple<String, string>> VehicleTypes =
		new SortedList<String, Tuple<String, string>>();
	// Vehicle Types defined in constructor (GameStatics())

	public const string DefaultScenarioPath = @"SumoImporter/DefaultEnv/DefaultGodotEnv.net.xml";
	public const string DefaultScenarioPath2 = @"SumoImporter/DefaultEnv/10Traffic100Buildings.net.xml";

	public const string StreetSingsBasePath = @"Environment/StreetSigns/";
	public const string NoEntrySignPath = StreetSingsBasePath + @"NoEntry/sign_no_entry.glb";
	public const string NoLeftTurnPath = StreetSingsBasePath + @"NoLeftTurn/sign_no_left_turn.glb";
	public const string NoRightTurnPath = StreetSingsBasePath + @"NoRightTurn/sign_no_right_turn.glb";
	public const string NoStraightOnPath = StreetSingsBasePath + @"NoStraightOn/sign_no_straight_on.glb";
	public const string OneWayLeftPath = StreetSingsBasePath + @"OneWayLeft/sign_one_way_left.glb";
	public const string OneWayRightPath = StreetSingsBasePath + @"OneWayRight/sign_one_way_right.glb";
	public const string OnlyLeftTurnPath = StreetSingsBasePath + @"OnlyLeftTurn/sign_only_left_turn.glb";
	public const string OnlyRightTurnPath = StreetSingsBasePath + @"OnlyRightTurn/sign_only_right_turn.glb";
	public const string PriorityPath = StreetSingsBasePath + @"Priority/sign_priority.glb";
	public const string SpeedLimit50Path = StreetSingsBasePath + @"SpeedLimit50/sign_speed_limit_50.glb";
	public const string SpeedLimit30Path = StreetSingsBasePath + @"SpeedLimit30/sign_speed_limit_30.glb";
	public const string StopPath = StreetSingsBasePath + @"Stop/sign_stop.glb";
	public const string YieldPath = StreetSingsBasePath + @"Yield/sign_yield.glb";


	public const float Rad90 = Mathf.Pi * 0.5f;
	public const float Rad180 = Mathf.Pi;

	public const int DefaultSeed = 4358234;

	public static NumberFormatInfo Provider = new NumberFormatInfo() { NumberDecimalSeparator = "." };
	public static VCEInstance GameInstance { get; private set; }

	public static Vector3 SumoOffset
	{
		get
		{
			if (GameInstance != null)
				return GameInstance.SUMONetworkGenerator.SumoOffset;
			else
				return Vector3.Zero;
		}
	}

	public static string NetOffset
	{
		get
		{
			if (GameInstance != null)
				return GameInstance.SUMONetworkGenerator.NetOffset;
			else
				return "";
		}
	}

	public static string ProjParameters
	{
		get
		{
			if (GameInstance != null)
				return GameInstance.SUMONetworkGenerator.ProjParameters;
			else
				return "";
		}
	}

	static GameStatics()
	{
		// The keys have to match with those used in MakeRegisterCommand in VehicleManager.
		VehicleTypes.Add(
			"BICYCLE",
			new Tuple<string, string>(
				"Bicycle",
				@"Vehicles/Bicycle/Bicycle.tscn"
			)
		);
		VehicleTypes.Add(
			"BICYCLE_WITH_MINIMAP",
			new Tuple<string, string>(
				"Bicycle with Minimap",
				@"Vehicles/Bicycle/BicycleWithMinimap.tscn"
			)
		);
		VehicleTypes.Add(
			"BICYCLE_INTERFACE",
			new Tuple<string, string>(
				"Bicycle Interface",
				@"Vehicles/Bicycle/InterfaceBicycle.tscn"
			)
		);
		VehicleTypes.Add(
			"CAR",
			new Tuple<string, string>(
				"Car",
				@"Vehicles/DefaultCar/Car.tscn"
			)
		);
	}

	public static void SetGameInstance(VCEInstance instance)
	{
		GameInstance = instance;
	}


}

