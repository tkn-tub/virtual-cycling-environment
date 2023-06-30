using Godot;
using System.Globalization;


/// <summary>
/// Class which holds a collection of static variables and constants
/// </summary>
public static class GameStatics
{
	public const string DefaultCarPath = @"Vehicles/DefaultCar/Car.tscn";
	public const string DefaultBicyclePath = @"Vehicles/Bicycle/Bicycle.tscn";
	public const string DynamicBuildingtPath = @"Environment/Buildings/DynamicBuilding.tscn";
	public const string TrafficLightPath = @"Environment/TrafficLight/TrafficLight.tscn";
	public const string TrafficLightPanelPath = @"Environment/TrafficLight/TrafficLightPanel.tscn";
	public const string TrafficLightPoleExtendPath = @"Environment/TrafficLight/Mesh/TrafficLight_Extend.mesh";
	public const string InterfaceBicyclePath = @"Vehicles/Bicycle/InterfaceBicycle.tscn";
	public const string BicycleWithMinimapPath = @"Vehicles/Bicycle/BicycleWithMinimap.tscn";



	public const string DefaultScenarioPath = @"SumoImporter/DefaultEnv/DefaultGodotEnv.net.xml";
	public const string DefaultScenarioPath2 = @"SumoImporter/DefaultEnv/10Traffic100Buildings.net.xml";
	public const string PaderbornScenarioPath = @"../scenarios/3denv-networks/paderborn-north-toj.net.xml";

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

	}

	public static void SetGameInstance(VCEInstance instance)
	{
		GameInstance = instance;
	}


}

