

using Godot;
using System;
using System.Collections.Generic;


public class BicycleInterfaceController : KinematicBody
{

	[Export]
	private float Acceleration = 0.0f;
	[Export]
	private float BreakForce = 15.0f;
	[Export]
	private float GroundFriction = 1.0f;
	[Export]
	private float MaxSpeed = 70f;
	[Export]
	private float SteeringRate = 1.0f;
	[Export]
	private bool bCanSteerInPlace = false;

	private Vector3 Velocity = new Vector3();
	private Vector3  _desiredLocation = new Vector3();
	private float Speed = 0.0f;
	private float SteeringAngle = 0.0f;
	public Vector3 lastRotation = new Vector3();
	public Vector3 lastPosition = new Vector3();


	// Class that updates the bicycle skeleton
	public BicycleRig bicycleRig;
	private int _speedWindowSize = 20;
	private List<float> _speedWindow;
	private bool started = false;
	private Vector3 _targetVelocity;
	private float _lastSpeed;

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

			_miniMapSpeedLabel = GetNode<Label3D>("bike_full/MiniMapView/SpeedLabel");
		}
		lastRotation = this.Rotation;
		lastPosition = this.Transform.origin;
		_lastSpeed = 0.0f;
		_speedWindow = new List<float>();
		_targetVelocity = new Vector3(0, 0, 0);
	}


	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(float delta)
	{


	}

	public override void _PhysicsProcess(float delta)
	{
		if(started == false){
			return;
		}
		
				//Update minimap camera
		if (_miniMapCamera != null)
		{
			_miniMapCamera.GlobalTransform = GlobalTransform;
		}
		
		// Retrieve angle between bicycle object and bicycle frame (always 0)
		float frame_angle = _skeleton.GetBonePose(_skeleton.FindBone("Frame")).basis.GetEuler().y;

		// Calculate the angle between handle and bicycle frame
		float handle_angle_to_frame = _skeleton.GetBonePose(_skeleton.FindBone("Handle")).basis.GetEuler().y - frame_angle;

		// Calculate desired handlle angle
		float remaining_angle = (frame_angle - SteeringAngle) - handle_angle_to_frame;
		
		// Update angle
		bicycleRig.SteeringAngle =  remaining_angle * delta;
	
		if(bCanSteerInPlace || Mathf.Abs(Speed) > 0.0f)
		{
			SteeringAngle = SteeringRate * delta * SteeringAngle;
			Rotation += new Vector3(0, SteeringAngle, 0);
		}
		
		
		float targetSpeed = 0.0f;
		Vector3 forwardVector = GetForwardVector();
		//Hard stop vehicle if speed is to low and no acceleration is applied
		if(Mathf.Abs(Speed) < 1.0f && Acceleration == 0.0f)
		{
			Speed = 0.0f;
		}
		else
		{	
			// Interpolate over previous bicycle speed in the simulation and adjust new speed based on new desired Speed (retrieved from physical speed sensor)
			float difference = Speed -  _lastSpeed;
			// Make sure that the change of speed is not too big (assures smooth movement in simulation)
			targetSpeed = _lastSpeed + (difference * delta);
			_lastSpeed = targetSpeed;
		}

		// Move bicycle in the simulation
		Vector3 targetVelocity = forwardVector * targetSpeed;
		Velocity = MoveAndSlide(targetVelocity , GetUpVector());
		float SpeedCurrent = Velocity.Length();
		bicycleRig.CurrentVelocity = SpeedCurrent;
		// Update minimap
		if (_miniMapSpeedLabel != null)
		{
			_miniMapSpeedLabel.Text = String.Format("{0} m/s", (int)(SpeedCurrent));
		}
	}
	
	// Called by networkListener class to update sensor data
	public void Update(Vector3 location, float speed, float acceleration, float steeringAngle_)
	{
		_desiredLocation.x = location.y;
		_desiredLocation.y = location.z;
		_desiredLocation.z = location.x;
		started = true;
		Acceleration = acceleration;
		Speed = speed;
		SteeringAngle = steeringAngle_; 
	}

	private float GetSpeedChange(float axisValue, float direction)
	{
		if(Mathf.Abs(axisValue) > 0 && direction == Mathf.Sign(axisValue)) //Apply acceleration
		{
			return axisValue * Acceleration * Mathf.Pow(1-Speed/MaxSpeed, 2.0f);
		}
		else if(Mathf.Abs(axisValue) > 0 && direction != Mathf.Sign(axisValue)) //Apply breaking force
		{
			return axisValue * BreakForce;
		}
		else //Apply drag force when vehicle is not accelerating
		{
			return -direction * GroundFriction * (1 - Speed/(MaxSpeed + 0.1f));
		}
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
