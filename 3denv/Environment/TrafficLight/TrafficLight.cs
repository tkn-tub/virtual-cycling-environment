using Godot;
using Env3d.SumoImporter.NetFileComponents;
using System;
using System.Collections.Generic;

public class TrafficLight : Spatial
{
	public List<TrafficLightPanel> Panels { get; private set; } = new List<TrafficLightPanel>();
	private static readonly PackedScene TrafficLightPanelScene = ResourceLoader.Load<PackedScene>(GameStatics.TrafficLightPanelPath);
	private static readonly Mesh TrafficLightPoleExtendMesh = ResourceLoader.Load<Mesh>(GameStatics.TrafficLightPoleExtendPath);

	const float TrafficPoleExtendLength = 2.5f;


	public override void _Ready()
	{
		
	}

	public void AddPanel(string PanelID, float Offset, int CurrentPanelIndex, int TotalPanels, connectionTypeDir Direction)
	{
		// TODO: use ct.dir to set arrows on the traffic lights!
		// http://sumo.dlr.de/wiki/Networks/SUMO_Road_Networks#Plain_Connections

		TrafficLightPanel newPanel = TrafficLightPanelScene.Instance<TrafficLightPanel>();
		newPanel.Translation = new Vector3(TrafficPoleExtendLength * Offset + 0.6f * (CurrentPanelIndex - TotalPanels/2.0f) + 0.4f, 0, 0);
		newPanel.ID = PanelID;
		newPanel.SetDirection(Direction);
		Panels.Add(newPanel);

		AddChild(newPanel);
	}

	public void AddPoolExtension(int PoistionIndex)
	{
		MeshInstance newPoleExtension = new MeshInstance();
		newPoleExtension.Translation = new Vector3(TrafficPoleExtendLength * PoistionIndex, 0, 0);
		newPoleExtension.Mesh = TrafficLightPoleExtendMesh;

		AddChild(newPoleExtension);

	}

}
