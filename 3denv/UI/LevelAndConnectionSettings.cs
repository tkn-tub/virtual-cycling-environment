using Godot;
using System;
using System.Collections.Generic;

public class LevelAndConnectionSettings : Control
{
	private FileDialog SumoNetworkFileDialog;
	private Button BSelectSumoScenario;
	private Button BRecordPerformance;
	private OptionButton SelectedVehicleTypeBtn;
	private LineEdit EgoVehicleNameEdit;
	private LineEdit EVIIPEdit;
	private LineEdit EVIPortEdit;
	private LineEdit SeedEdit;
	private CheckBox StreetLightsCheckbox;

	// relative to VCE_ROOT:
	private string SelectedSumoNetFile = @"scenarios/3denv-networks/paderborn-north.net.xml";

	private bool ConnectEVIOnLaunch = false;

	private bool SkipMenu = false;

	/// <summary>
	/// Returns the key of the selected vehicle type,
	/// e.g., "BICYCLE_WITH_MINIMAP".
	/// </summary>
	public string GetSelectedVehicleType()
	{
		return GameStatics.VehicleTypes.Keys[
			SelectedVehicleTypeBtn.GetSelectedId()
		];
	}

	public string GetSelectedSumoNetFile()
	{
		return SelectedSumoNetFile;
	}

	public int GetSeed()
	{
		return int.Parse(SeedEdit.Text);
	}

	public bool GetStreetLightsChecked()
	{
		return StreetLightsCheckbox.Pressed;
	}

	public bool GetConnectToEVIOnLaunch()
	{
		return ConnectEVIOnLaunch;
	}

	public bool GetSkipMenu()
	{
		return SkipMenu;
	}

	public string GetEVIAddress()
	{
		return EVIIPEdit.Text;
	}

	public int GetEVIPort()
	{
		return int.Parse(EVIPortEdit.Text);
	}

	public string GetEgoVehicleName()
	{
		return EgoVehicleNameEdit.Text;
	}

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		// Set SelectedSumoNetFile depending on whether we're running in the editor
		if (OS.HasFeature("editor"))
		{
			// Assuming we are in VCE_ROOT/3denv/
			GD.Print("Seems we are running in the editor");
			SelectedSumoNetFile = "../" + SelectedSumoNetFile;
		} else {
			// Assuming we are in VCE_ROOT/3denv/build/
			GD.Print("Seems we are running an exported game");
			SelectedSumoNetFile = "../../" + SelectedSumoNetFile;
		}

		var cmdLineArgs = ParseCmdLineArgs();

		foreach (Control child in GetAllChildren(this))
		{
			switch (child.Name)
			{
				case "BSelectSumoScenario":
					BSelectSumoScenario = (Button)child;
					break;

				case "SumoNetworkSelector":
					SumoNetworkFileDialog = (FileDialog)child;
					SumoNetworkFileDialog.CurrentPath = SelectedSumoNetFile;
					break;

				case "VehicleTypeSelection":
					SelectedVehicleTypeBtn = (OptionButton)child;
					foreach (var vtype in GameStatics.VehicleTypes)
					{
						SelectedVehicleTypeBtn.AddItem(
							vtype.Value.Item1,
							GameStatics.VehicleTypes.IndexOfKey(vtype.Key)
						);
					}
					SelectedVehicleTypeBtn.Select(
						GameStatics.VehicleTypes.IndexOfKey(
							cmdLineArgs.ContainsKey("vehicle-type") ?
							cmdLineArgs["vehicle-type"] :
							"BICYCLE_WITH_MINIMAP"
						)
					);
					break;

				case "LineEditEgoName":
					EgoVehicleNameEdit = (LineEdit)child;
					EgoVehicleNameEdit.Text += new Random().Next(99999999);
					break;

				case "LineEditEVIIP":
					EVIIPEdit = (LineEdit)child;
					EVIIPEdit.Text =
						cmdLineArgs.ContainsKey("evi-address") ?
						cmdLineArgs["evi-address"] :
						"localhost";
					break;

				case "LineEditEVIPort":
					EVIPortEdit = (LineEdit)child;
					EVIPortEdit.Text =
						cmdLineArgs.ContainsKey("evi-port") ?
						cmdLineArgs["evi-port"] :
						"12346";
					break;

				case "LineEditSeed":
					SeedEdit = (LineEdit)child;
					SeedEdit.Text = 
						cmdLineArgs.ContainsKey("scenario-seed") ?
						cmdLineArgs["scenario-seed"] :
						GameStatics.DefaultSeed.ToString();
					break;

				case "CheckBoxStreetLights":
					StreetLightsCheckbox = (CheckBox)child;
					break;

				case "BRecordPerformance":
					BRecordPerformance = (Button)child;
					break;
			}
		}
	}

	public Dictionary<String, String> ParseCmdLineArgs()
	{
		var args = new Dictionary<string, string>();
		foreach (String arg in Godot.OS.GetCmdlineArgs())
		{
			if (!arg.Contains("="))
			{
				args.Add(arg, "");
			}
			var kv = arg.Split('=');
			args.Add(kv[0].TrimStart('-'), kv[1]);
		}

		// print parsed args:
		GD.Print("The following command line args have been parsed:");
		foreach (var arg in args)
		{
			GD.Print($"{arg.Key}: {arg.Value}");
		}

		if (
			args.ContainsKey("help")
			|| args.ContainsKey("h")
			|| args.ContainsKey("vce-help")
		){
			// This doesn't work with --help or -h,
			// since Godot will show its own
			// help before running any of our code.
			GD.Print(
				"""
				3D Environment of the Virtual Cycling Environment

				Usage: 3denv [Godot options] -- [3DEnv options]

				3DEnv options:
				  --scenario=<scenario>	       A SUMO .net.xml scenario to load on startup.
				  --scenario-seed=<seed>       An integer seed for the procedural generation of buildings, etc.
				  --vehicle-type=<vtype>       {"Bicycle", "Bicycle with minimap"}
				  --evi-address=<address>      Address (usually IP) of the Ego Vehicle Interface
				  --evi-port=<port>            EVI Port
				  --evi-connect-on-launch=True Connect to EVI immediately
				  --skip-menu=True             Don't show menu on launch
				"""
			);
			GetTree().Quit();
		}
		SkipMenu = args.ContainsKey("skip-menu");
		ConnectEVIOnLaunch = args.ContainsKey("evi-connect-on-launch");
		if (args.ContainsKey("scenario")) SelectedSumoNetFile = args["scenario"];
		return args;
	}

	public List<Control> GetAllChildren(Control ParentControl)
	{
		List<Control> children = new List<Control>();
		foreach (System.Object child in ParentControl.GetChildren())
		{
			Control control = child as Control;
			if (control != null)
			{
				children.Add(control);
				children.AddRange(GetAllChildren(control));
			}
		}
		return children;
	}

	private void _on_VehicleTypeSelection_item_selected(int index)
	{
		GameStatics.GameInstance.ChangePlayerVehicle(
			GameStatics.VehicleTypes.Values[index].Item2
			// Item2 is the resource path, Item1 the Vehicle Type description
		);
	}


	private void _on_BSelectSumoScenario_pressed()
	{
		SumoNetworkFileDialog.Popup_();
	}

	private void _on_SumoNetworkSelector_confirmed()
	{
		SelectedSumoNetFile = SumoNetworkFileDialog.CurrentPath + SumoNetworkFileDialog.Filename;
		BSelectSumoScenario.Text = SumoNetworkFileDialog.CurrentFile.Replace(".net.xml", "");
	}

	private void _on_BGenerateNetwork_pressed()
	{
		int seed = int.Parse(SeedEdit.Text);
		GameStatics.GameInstance.GenerateNetwork(
			SelectedSumoNetFile,
			seed,
			StreetLightsCheckbox.Pressed
		);
	}

	private void _on_BCloseMenu_pressed()
	{
		GameStatics.GameInstance.SetMenuVisibility(false);
	}

	private void _on_BExit_pressed()
	{
		GetTree().Quit();
	}

	private void _on_BConnectToEVI_pressed()
	{
		GameStatics.GameInstance.ConnectToEVI(
			EgoVehicleNameEdit.Text,
			EVIIPEdit.Text,
			GetEVIPort(),
			GetSelectedVehicleType() // TODO: use key, not description!
		);
	}

	private void _on_BRecordPerformance_pressed()
	{
		if(GameStatics.GameInstance.TooglePerformanceMeasurement())
		{
			BRecordPerformance.Text = "Stop";
		}
		else
		{
			BRecordPerformance.Text = "Start";
		}
	}
}
