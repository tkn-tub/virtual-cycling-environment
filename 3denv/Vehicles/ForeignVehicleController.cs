using Godot;
using extrapolation;
using Asmp.Vehicle;
public class ForeignVehicleController : KinematicBody
{


	private Spatial _wheelFrontLeft;
	private Spatial _wheelFrontRight;
	private Spatial _wheelRearLeft;
	private Spatial _wheelRearRight;
	private Spatial[] _wheels;
	private MeshInstance[] _caseMeshes;
	public double wheelRadius = .33;
	public double vehicleSpeed = 0;
	public float steeringAngleApproximationFactor = 6f;
	public Vector3 targetTranslation;
	public Quat targetRotation;
	public Vector3 rotation;
	public Vector3 translation;
	public double angleDeg; // 0 is North
	
	public uint vehicleId;
	public string edgeId;
	public uint laneNum;
	public uint laneId;
	
	public NetFileLane lane;
	
	public bool isEgoVehicle;
	public RegisterVehicleCommand.Types.VehicleType vehicleType;

	public bool TurnLeftSignalOn;
	public bool TurnRightSignalOn;
	public float passedDeltaTime =  0.0f;

	public OmniLight signalLeft;
	public OmniLight signalRight;
	public OmniLight signalStop;

	private BicycleRig bicycleRig;

	public override void _Ready()
	{
		((SkeletonIK)FindNode("LeftFootIK"))?.Start();
		((SkeletonIK)FindNode("RightFootIK"))?.Start();
		// Seems like we can't get the steering angle for fellow traffic?
		// In that case, let's save on computing resources by not turning
		// on IK for the hands:
		// ((SkeletonIK)FindNode("LeftHandIK"))?.Start();
		// ((SkeletonIK)FindNode("RightHandIK"))?.Start();
		bicycleRig = GetNode<BicycleRig>("bike_full");
	}

	public override void _PhysicsProcess(float delta)
	{
		if (!targetRotation.IsNormalized()) // Make sure we start interpolating after receiving the first update message from SUMO
		{
			//GD.Print("Not normalized");
			return;
		}
		float interpolationWeight = 0.095f;
		this.Translation = this.Translation.LinearInterpolate(targetTranslation, interpolationWeight);
		translation = this.Translation;
		Quat currentRotation = new Quat(this.Rotation).Normalized();
		Quat interpolatedRotation = currentRotation.Slerp(targetRotation, interpolationWeight);
		this.Rotation = interpolatedRotation.GetEuler();
		rotation = this.Rotation;

		float deltaYaw = interpolatedRotation.GetEuler().y - currentRotation.GetEuler().y;
		UpdateWheels(delta, deltaYaw);
		updateSignals(delta);

		if (bicycleRig != null)
		{
			bicycleRig.SteeringAngle = deltaYaw;
			bicycleRig.CurrentVelocity = (float)vehicleSpeed;
		}
	}

	public void updateSignalsBool(bool turnSignalLeftOn, bool turnSignalRightOn)
	{
		if (this.vehicleType == RegisterVehicleCommand.Types.VehicleType.PassengerCar)
		{
			this.TurnLeftSignalOn = turnSignalLeftOn;
			this.TurnRightSignalOn = turnSignalRightOn;
		}
	}

	public void updateStopLight(bool signalStop)
	{
		if (this.vehicleType == RegisterVehicleCommand.Types.VehicleType.PassengerCar)
		{
			this.signalStop.Visible = signalStop;
		}
	}
	
	public void updateIsEgoVehicle(bool egoVehicle)
	{
		this.isEgoVehicle = egoVehicle;
	}

	private void updateSignals(float delta)
	{
		if (this.vehicleType == RegisterVehicleCommand.Types.VehicleType.Bicycle)
		{
			// TODO
		}
		else 
		{
			// Assuming PassengerCar or similar

			if (this.TurnLeftSignalOn == true)
			{
				
				if(this.passedDeltaTime > 0.5f)
				{
					this.signalLeft.Visible = !this.signalLeft.Visible;
					this.passedDeltaTime = 0.0f;
				}
				else
				{
					this.passedDeltaTime += delta;
				}
			}
			else
			{
				this.signalLeft.Visible = false; 
			}

			if (this.TurnRightSignalOn == true)
			{
				
				if(this.passedDeltaTime > 0.5f)
				{
					this.signalRight.Visible = !this.signalRight.Visible;
					this.passedDeltaTime = 0.0f;
				}
				else
				{
					this.passedDeltaTime += delta;
				}
			}
			else{
				this.signalRight.Visible = false;
			}
		}
	}


	public virtual void UpdateWheels(float delta, float angleRad = 0) { }

	public virtual void ChangeColor(Color color) { }

	public Vector3 GetForwardVector()
	{
		return GetRotationVector(Rotation);
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
