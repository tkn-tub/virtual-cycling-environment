using Godot;
using Source.SUMOImporter.NetFileComponents;
using System;

public class TrafficLightPanel : Spatial
{
	public static readonly Material LightsLeft = ResourceLoader.Load<Material>("Environment/TrafficLight/Mesh/TrafficLightPanelLeft.material");
	public static readonly Material LightsRight = ResourceLoader.Load<Material>("Environment/TrafficLight/Mesh/TrafficLightPanelRight.material");

	private string _id;
	public string ID 
	{ 
		get
		{
			return _id;
		}
		set
		{
			_id = value;
			GameStatics.GameInstance.TrafficLightsManager.AddTrafficLightPanel(this);
		}
	}

	private OmniLight RedLight;
	private OmniLight YellowLight;
	private OmniLight GreenLight;

	private TrafficLightState _lightState = TrafficLightState.TLState_BlinkYellow;
	public TrafficLightState LightState 
	{ 
		get { return _lightState; }
		set 
		{ 
			_lightState = value;
			switch (_lightState)
			{
				case TrafficLightState.TLState_Green:
					RedLight.Visible = false;
					YellowLight.Visible = false;
					GreenLight.Visible = true;
					break;

				case TrafficLightState.TLState_Yellow:
					RedLight.Visible = false;
					YellowLight.Visible = true;
					GreenLight.Visible = false;
					break;

				case TrafficLightState.TLState_Red:
					RedLight.Visible = true;
					YellowLight.Visible = false;
					GreenLight.Visible = false;
					break;

				case TrafficLightState.TLState_RedYellow:
					RedLight.Visible = true;
					YellowLight.Visible = true;
					GreenLight.Visible = false;
					break;
			}
		}
	}

	public override void _Ready()
	{
		RedLight = GetNode<OmniLight>("Panel/Light_Red");
		YellowLight = GetNode<OmniLight>("Panel/Light_Yellow");
		GreenLight = GetNode<OmniLight>("Panel/Light_Green");


		RedLight.Visible = false;
		YellowLight.Visible = false;
		GreenLight.Visible = false;

	}

	public void SetDirection(connectionTypeDir direction)
	{
		MeshInstance Panel = GetNode<MeshInstance>("Panel");

		switch (direction)
		{
			case connectionTypeDir.l:
				Panel.MaterialOverride = LightsLeft;
				break;
				

			case connectionTypeDir.r:
				Panel.MaterialOverride = LightsRight;
				break;
		}
	}

	private float passedDeltaTime =  0.0f;
	public override void _Process(float delta)
	{
		base._Process(delta);

		if (LightState == TrafficLightState.TLState_BlinkYellow)
		{
			if(passedDeltaTime > 0.5f)
			{
				YellowLight.Visible = !YellowLight.Visible;
				passedDeltaTime = 0.0f;
			}
			else
			{
				passedDeltaTime += delta;
			}
		}
	}

}


public enum TrafficLightState
{
	TLState_Green = 0,
	TLState_Yellow = 1,
	TLState_Red = 2,
	TLState_RedYellow = 3,
	TLState_BlinkYellow = 4
}
