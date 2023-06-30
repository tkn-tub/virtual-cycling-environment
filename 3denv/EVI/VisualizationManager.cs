using Godot;
using System;
using System.Collections.Generic;


public class VisualizationManager : Spatial
{

	private CoordinateTransformation _coordinateTransformation;
	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		Vector3 sumoOffset = GameStatics.SumoOffset;
				// WGS84 to Cartesian projection
		_coordinateTransformation = new CoordinateTransformation(
			GameStatics.NetOffset,
			GameStatics.ProjParameters,
			-sumoOffset.x,
			sumoOffset.z
		);
		
	}


	public void ExtractVisualizationUpdate(Asmp.Visualization.Message visualizationMsg)
{
	var result = new Dictionary<uint, VisualizationData>();
	int visualizationCommandCount = visualizationMsg.Commands.Count;
	for (int i = 0; i < visualizationCommandCount; ++i)
	{
		var command = visualizationMsg.Commands[i];
		if (command.CommandOneofCase == Asmp.Visualization.Command.CommandOneofOneofCase.GenericWarning)
		{
			result.Add(command.EntityId,
				new GenericWarning(command.EntityId, command.GenericWarning.Intensity,
					command.GenericWarning.Description));
		}
		else if (command.CommandOneofCase == Asmp.Visualization.Command.CommandOneofOneofCase.WirelessMessage)
		{
			result.Add(command.EntityId,
				new ReceivedWirelessMessage(command.EntityId, command.WirelessMessage.SenderId,
					visualizationMsg.TimeS, command.WirelessMessage.Location.Px,
					command.WirelessMessage.Location.Py, command.WirelessMessage.Location.Angle,
					command.WirelessMessage.Location.Lon, command.WirelessMessage.Location.Lat));
		}
		else
		{
			GD.PushWarning("Unknown visualization command");
		}
	}
	UpdateVisualizationCommands(result);
}
	
	private void UpdateVisualizationCommands(Dictionary<uint, VisualizationData> visualizationData)
	{
		foreach (VisualizationData vd in visualizationData.Values)
		{
			if (vd is GenericWarning)
			{
				// GenericWarning gw = (GenericWarning)vd;
				// if (gw.entityId == egoVehicleHashId)
				// {
				//     //MonoBehaviour.print ("activating led" + gw.entityId.ToString () + "egoVehicleHashId: " + egoVehicleHashId.ToString ());
				//     //Flash red warning led
				//     if (!isBicycle)
				//     {
				//         GenericWarningLedCar.SetActive(true);
				//         GenericWarningCanvas.SetActive(true);
				//     }
				//     else
				//     {
				//         GenericWarningLedBicycleLeft.SetActive(true);
				//         GenericWarningLedBicycleRight.SetActive(true);
				//     }

				//     //Play warning sound
				//     GenericWarningAudioSource.PlayOneShot(GenericWarningSound, 0.5f);

				//     //Display Warning in Textarea
				//     GenericWarningTextarea.GetComponent<Text>().text = gw.description;
				//     warningTimer.Start();
				// }
			}
			else if (vd is ReceivedWirelessMessage)
			{
				ReceivedWirelessMessage rwm = (ReceivedWirelessMessage)vd;
				InstantiateNewWirelessMessageIndicator(rwm);
			}
			else
			{
				GD.PushWarning("unknown visualizationData");
			}
		}
	}
	
	private void InstantiateNewWirelessMessageIndicator(ReceivedWirelessMessage pRWM)
{
	PackedScene miniMapArrowScene = ResourceLoader.Load<PackedScene>("res://Vehicles/MiniMapArrow/MiniMapArrow.tscn");
	MiniMapArrow arrow = miniMapArrowScene.Instance<MiniMapArrow>();

	// Extract plain data from message encoding (which follows CAM message encoding)
	float angle = (float)-pRWM.angle - 90f;
	Vector3 sumo_pos = _coordinateTransformation.WGS84ToCartesianProj(pRWM.lon, pRWM.lat, 0);
	arrow.Translation = new Vector3(-sumo_pos.x, 0, sumo_pos.z);
	GD.Print($"Spawning indicator arrow at {arrow.Translation} (lon {pRWM.lon}, lat {pRWM.lat}");
	arrow.Rotation = new Vector3(0f, Mathf.Deg2Rad(angle), 0f);
	Color yellow = new Color(1f, 1f, 0f);
	arrow.ChangeColor(yellow);
	AddChild(arrow);
}



}
