

using Godot;
using System;
using System.Collections.Generic;


public class BicycleInterfaceController : KinematicBody
{
	private Vector3 Velocity = new Vector3();
	private Vector3 _desiredLocation = new Vector3();
	private float Speed = 0.0f;
	private float SteeringAngle = 0.0f;
	private float _desiredYaw = 0f;
	private Vector3 StartPosition;


	// Class that updates the bicycle skeleton.
	public BicycleRig MBicycleRig;
	private bool started = false;

	// Skeleton of the bicycle model
	private Skeleton _skeleton;
	public Skeleton Skeleton
	{
		get { return _skeleton; }
		set { _skeleton = value; }
	}

	public float GetSpeed()
	{
		return Speed;
	}

	public Vector3 GetVelocity()
	{
		return Velocity;
	}
	
	private Spatial _miniMapCamera;
	private Label3D _miniMapSpeedLabel;

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
		// Attach minimap
		_miniMapCamera = GetNodeOrNull<Spatial>("Viewport/DummyCamera");
		if (_miniMapCamera != null)
		{
			PackedScene miniMapArrowScene = ResourceLoader.Load<PackedScene>("res://Vehicles/MiniMapArrow/MiniMapArrow.tscn");
			MiniMapArrow arrow = miniMapArrowScene.Instance<MiniMapArrow>();
			arrow.SetIsPlayerArrow(true);
			AddChild(arrow);

			_miniMapSpeedLabel = GetNode<Label3D>("bike_full/Bicycle CCS Armature/Skeleton/HandleAttachment/MiniMapView/SpeedLabel");
		}
		MBicycleRig = GetNode<BicycleRig>("bike_full"); 
		Skeleton = MBicycleRig.GetNode<Skeleton>("Bicycle CCS Armature/Skeleton");
		StartPosition = GlobalTranslation;
	}


	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(float delta)
	{


	}

	public override void _PhysicsProcess(float delta)
	{
		if (started == false)
		{
			return;
		}
		
		//Update minimap camera
		if (_miniMapCamera != null)
		{
			_miniMapCamera.GlobalTransform = GlobalTransform;
		}
		
		this.GlobalTranslation = _desiredLocation; // TODO: interpolate
		this.Rotation = new Vector3(0, _desiredYaw, 0);
		
		// Update minimap
		if (_miniMapSpeedLabel != null)
		{
			_miniMapSpeedLabel.Text = $"{(int)(3.6 * Speed)} km/h";
		}
	}
	
	// Called by networkListener class to update sensor data
	public void Update(
		Vector3 location,
		float yaw,
		float speed,
		float acceleration,
		float steeringAngle_
	){
		// TODO: missing yaw, pitch, roll
		_desiredLocation = new Vector3(
			location.y,
			location.z,
			location.x
		) + StartPosition;
		started = true;
		Speed = speed;
		MBicycleRig.CurrentVelocity = speed;
		MBicycleRig.SteeringAngle = steeringAngle_;
		_desiredYaw = yaw;
	}

	public Vector3 GetForwardVector()
	{
		return GetRotationVector(Rotation);
	}

	public Vector3 GetUpVector()
	{
		if(Mathf.IsZeroApprox(Rotation.z))
		{
			return Vector3.Up;
		}
		else
		{
			return GetRotationVector(Rotation + new Vector3(0, 0, GameStatics.Rad90));
		}
	}

	public Vector3 GetRightVector()
	{
		return GetRotationVector(Rotation + new Vector3(0, GameStatics.Rad90, 0));
	}

	private static Vector3 GetRotationVector(Vector3 Rotator)
	{
		float Pitch = (Rotator.z);
		float Yaw = (-Rotator.y);
		
		float sinP = Mathf.Sin(Pitch);
		float sinY = Mathf.Sin(Yaw);
		float cosY = Mathf.Cos(Yaw);
		float cosP = Mathf.Cos(Pitch);
	
		return new Vector3(cosY*cosP, sinP, cosP*sinY);
	}
}
