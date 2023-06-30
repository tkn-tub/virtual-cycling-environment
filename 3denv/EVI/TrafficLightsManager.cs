using Godot;
using System;
using System.Collections.Generic;

public class TrafficLightsManager
{
	public void Init()
	{

	}

	public Dictionary<string, TrafficLightPanel> TrafficLightPanels = new Dictionary<string, TrafficLightPanel>();

	public bool AddTrafficLightPanel(TrafficLightPanel Panel)
	{
		if(TrafficLightPanels.ContainsKey(Panel.ID))
		{
			return false;
		}
		else
		{
			TrafficLightPanels.Add(Panel.ID, Panel);
			return true;
		}
	}
	// Extract desired traffic light state (e.g. red light, green light)

	public void ExtractTrafficLightUpdate(Asmp.Trafficlight.Message trafficlightMsg)
	{
		var result = new Dictionary<uint, TrafficlightData>();
		int junctionCount = trafficlightMsg.Junctions.Count;
		for (int i = 0; i < junctionCount; ++i)
		{
			var junction = trafficlightMsg.Junctions[i];
			string signals = "";
			int signalCount = junction.Signals.Count;
			for (int k = 0; k < signalCount; ++k)
			{
				var signal = junction.Signals[k];
				if (signal.State == Asmp.Trafficlight.Signal.Types.SignalState.Off)
				{
					signals += "o";
				}
				else if (signal.State == Asmp.Trafficlight.Signal.Types.SignalState.Red)
				{
					signals += "r";
				}
				else if (signal.State == Asmp.Trafficlight.Signal.Types.SignalState.RedYellow)
				{
					signals += "a";
				}
				else if (signal.State == Asmp.Trafficlight.Signal.Types.SignalState.Green)
				{
					signals += "g";
				}
				else if (signal.State == Asmp.Trafficlight.Signal.Types.SignalState.Yellow)
				{
					signals += "y";
				}
				else
				{
					throw new Exception();
				}
			}

			result.Add(junction.Id, new TrafficlightData(junction.Id, signals));
		}


		UpdateTrafficLights(result);
	}


	// Apply changes in traffic light state 

	public void UpdateTrafficLights(Dictionary<uint, TrafficlightData> trafficlightData)
	{
		foreach (TrafficlightData tld in trafficlightData.Values)
		{

			for (int i = 0; i < tld.signals.Length; i++)
			{

				TrafficLightPanel tlp;
				if(TrafficLightPanels.TryGetValue("tl_" + tld.tlId + "_" + i, out tlp))
				{
					switch (tld.signals.Substring(i, 1))
					{
						case "g":
							tlp.LightState = TrafficLightState.TLState_Green;
							break;
						case "y":
							tlp.LightState = TrafficLightState.TLState_Yellow;
							break;
						case "r":
							tlp.LightState = TrafficLightState.TLState_Red;
							break;
						case "o":
							tlp.LightState = TrafficLightState.TLState_BlinkYellow;
							break;
						case "u":
							tlp.LightState = TrafficLightState.TLState_RedYellow;
							break;

						default:
							tlp.LightState = TrafficLightState.TLState_BlinkYellow;
							break;
					}
				}
				else
				{
					GD.Print("Traffic light not found: " + "tl_" + tld.tlId + "_" + i);
				}
			}
		}
	}

}
