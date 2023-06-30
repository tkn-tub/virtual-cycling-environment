using Godot;
using System;
using System.Collections.Generic;

public class LevelAndConnectionSettings : Control
{
	private FileDialog SumoNetworkSelector;
	private Button BSelectSumoScenario;
	private Button BRecordPerformance;
	private OptionButton SelectedVehicleType;
	private LineEdit EgoVehicleName;
	private LineEdit EVIIP;
	private LineEdit EVIPort;
	private LineEdit Seed;
	private CheckBox StreetLights;

	private string SelectedSumoNetFile = @"Assets\DefaultEnv\DefaultGodotEnv.net.xml";
	public string GetSelectedVehicleType()
	{
		return SelectedVehicleType.GetItemText(SelectedVehicleType.Selected);
	}
	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{

		foreach (Control child in GetAllChildren(this))
		{
			switch (child.Name)
			{
				case "BSelectSumoScenario":
					BSelectSumoScenario = (Button)child;
					break;

				case "SumoNetworkSelector":
					SumoNetworkSelector = (FileDialog)child;
					SumoNetworkSelector.CurrentPath = @"../scenarios/";
					break;

				case "VehicleTypeSelection":
					SelectedVehicleType = (OptionButton)child;
					SelectedVehicleType.AddItem("Bicycle", 0);
					SelectedVehicleType.AddItem("Bicycle with Minimap", 1);
					SelectedVehicleType.AddItem("Bicycle_Interface", 2);
					SelectedVehicleType.AddItem("Car", 3);
					SelectedVehicleType.Select(0);
					break;

				case "LineEditEgoName":
					EgoVehicleName = (LineEdit)child;
					EgoVehicleName.Text += new Random().Next(99999999);
					break;

				case "LineEditEVIIP":
					EVIIP = (LineEdit)child;
					break;

				case "LineEditEVIPort":
					EVIPort = (LineEdit)child;
					break;

				case "LineEditSeed":
					Seed = (LineEdit)child;
					Seed.Text = GameStatics.DefaultSeed.ToString();
					break;

				case "CheckBoxStreetLights":
					StreetLights = (CheckBox)child;
					break;

				case "BRecordPerformance":
					BRecordPerformance = (Button)child;
					break;


			}
		}
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
		switch (index)
		{
			case 0:
				GameStatics.GameInstance.ChangePlayerVehicle(GameStatics.DefaultBicyclePath);
				break;

			case 1:
				GameStatics.GameInstance.ChangePlayerVehicle(GameStatics.BicycleWithMinimapPath);
				break;	

			case 2:
				GameStatics.GameInstance.ChangePlayerVehicle(GameStatics.InterfaceBicyclePath);
				break;

			case 3:
				GameStatics.GameInstance.ChangePlayerVehicle(GameStatics.DefaultCarPath);
				break;
		}
	}


	private void _on_BSelectSumoScenario_pressed()
	{
		SumoNetworkSelector.Popup_();
	}

	private void _on_SumoNetworkSelector_confirmed()
	{
		SelectedSumoNetFile = SumoNetworkSelector.CurrentPath + SumoNetworkSelector.Filename;
		BSelectSumoScenario.Text = SumoNetworkSelector.CurrentFile.Replace(".net.xml", "");
	}

	private void _on_BGenerateNetwork_pressed()
	{
		int seed = int.Parse(Seed.Text);
		GameStatics.GameInstance.GenerateNetwork(SelectedSumoNetFile, seed, StreetLights.Pressed);
	}

	private void _on_BCloseMenu_pressed()
	{
		GameStatics.GameInstance.ToggleMenu();
	}

	private void _on_BConnectToEVI_pressed()
	{
		GameStatics.GameInstance.ConnectToEVI(EgoVehicleName.Text, EVIIP.Text, EVIPort.Text, SelectedVehicleType.Text);
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

