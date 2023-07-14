using Godot;
using System;
public class SimpleVehicleController : KinematicBody
{

	[Export]
	private float Acceleration = 5.0f;
	[Export]
	private float BreakForce = 15.0f;
	[Export]
	private float GroundFriction = 1.0f;
	[Export]
	private float MaxSpeed = 70f;
	[Export]
	private float SteeringRate = 5.0f;
	[Export]
	private bool bCanSteerInPlace = false;

	private Vector3 Velocity = new Vector3();
	private float Speed = 0.0f;
	private float SteeringAngle = 0.0f;

	private BicycleRig MBicycleRig;

	private Spatial _miniMapCamera;
	private Label3D _miniMapSpeedLabel;
	public float GetSpeed()
	{
		return Speed;
	}

	public Vector3 GetVelocity()
	{
		return Velocity;
	}

	// Called when the node enters the scene tree for the first time.
	public override void _Ready()
	{
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
	}


	// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(float delta)
	{
		float turnAxis = Input.GetAxis("MoveRight", "MoveLeft");
		if (bCanSteerInPlace || Speed > 0.0f)
		{
			/*SteeringAngle = Mathf.Lerp(
				SteeringAngle,
				SteeringRate * turnAxis * delta,
				turnAxis == 0 ? 0.5f : 0.1f
			);*/
			var adjustSteering = turnAxis * Mathf.Deg2Rad(15f) - SteeringAngle; // remaining different for SteeringAngle to reach
			const float steeringSensitivity = 0.5f; // 0: no effect, -1: 50 %, 1: 200 %
			SteeringAngle += adjustSteering * delta * 3.0f * Mathf.Pow(2, steeringSensitivity);
			
			Rotation += new Vector3(0, SteeringAngle * delta * 10f, 0);
		}
	}

	public override void _PhysicsProcess(float delta)
	{
		// Update minimap camera
		if (_miniMapCamera != null)
		{
			_miniMapCamera.GlobalTransform = GlobalTransform;
		}

		float forwardAxis = Input.GetAxis("MoveBack", "MoveForward");
		float direction = 1.0f;
		Vector3 forwardVector = GetForwardVector();
		// Determine direction by checking if velocity is alligned with forward vector
		if (Speed > 0)
		{
			direction = (Velocity / Speed).Dot(forwardVector);
		}

		// Hard stop vehicle if speed is too low and no acceleration is applied
		if (Mathf.Abs(Speed) < 1.0f && forwardAxis == 0.0f)
		{
			Speed = 0.0f;
		}
		else
		{
			float targetSpeed = Speed * direction + GetSpeedChange(forwardAxis, Mathf.Sign(direction)) * delta;
			Vector3 targetVelocity = forwardVector * targetSpeed;

			Velocity = MoveAndSlide(targetVelocity, GetUpVector());
			Speed = Velocity.Length();

			// Update minimap speed label if applicable
			if (_miniMapSpeedLabel != null)
			{
				_miniMapSpeedLabel.Text = $"{(int)(3.6 * direction * Speed)} km/h";
			}
		}

		if (MBicycleRig != null)
		{
			MBicycleRig.SteeringAngle = SteeringAngle;
			MBicycleRig.CurrentVelocity = Speed * direction;
		} // else car
	}

	private float GetSpeedChange(float axisValue, float direction)
	{
		if (Mathf.Abs(axisValue) > 0 && direction == Mathf.Sign(axisValue)) //Apply acceleration
		{
			return axisValue * Acceleration * Mathf.Pow(1 - Speed / MaxSpeed, 2.0f);
		}
		else if (Mathf.Abs(axisValue) > 0 && direction != Mathf.Sign(axisValue)) // Apply breaking force
		{
			return axisValue * BreakForce;
		}
		else // Apply drag force when vehicle is not accelerating
		{
			return -direction * GroundFriction * (1 - Speed / (MaxSpeed + 0.1f));
		}
	}

	public Vector3 GetForwardVector()
	{
		return GetRotationVector(Rotation);
	}

	public Vector3 GetUpVector()
	{
		if (Mathf.IsZeroApprox(Rotation.z))
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

		return new Vector3(cosY * cosP, sinP, cosP * sinY);
	}
}
