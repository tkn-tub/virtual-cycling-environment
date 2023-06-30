using Godot;
using extrapolation;
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
	
	public uint vehicleId;
	public string edgeId;
	public uint laneNum;
	public uint laneId;
	
	public NetFileLane lane;
	
	public bool isEgoVehicle;

	public bool TurnLeftSignalOn;
	public bool TurnRightSignalOn;
	public float passedDeltaTime =  0.0f;

	public OmniLight signalLeft;
	public OmniLight signalRight;
	public OmniLight signalStop;


	public override void _PhysicsProcess(float delta)
	{
		if (!targetRotation.IsNormalized()) // Make sure we start interpolating after receiving the first update message from SUMO
		{
			//GD.Print("Not normalized");
			return;
		}
		float interpolationWeight = 0.095f;
		this.Translation = this.Translation.LinearInterpolate(targetTranslation, interpolationWeight);
		translation = this.Translation.LinearInterpolate(targetTranslation, interpolationWeight);
		Quat currentRotation = new Quat(this.Rotation).Normalized();
		Quat interpolatedRotation = currentRotation.Slerp(targetRotation, interpolationWeight);
		this.Rotation = interpolatedRotation.GetEuler();
		rotation = interpolatedRotation.GetEuler();


		float deltaYaw = interpolatedRotation.GetEuler().y - currentRotation.GetEuler().y;
		UpdateWheels(delta, deltaYaw);
		updateSignals(delta);

	}
	public void updateSignalsBool(bool turnSignalLeftOn, bool turnSignalRightOn){
		// GD.Print("blinkuje");
		// OmniLight signalLeft = this.GetNode<OmniLight>("Car/TurnLeftSignal");
		// signalLeft.Visible = turnSignalLeftOn;
		// OmniLight signalRight = this.GetNode<OmniLight>("Car/TurnRightSignal");
		// signalRight.Visible = turnSignalRightOn;
		this.TurnLeftSignalOn = turnSignalLeftOn;
		this.TurnRightSignalOn = turnSignalRightOn;
	}

	public void updateStopLight(bool signalStop){
		this.signalStop.Visible = signalStop;
	}
	
	public void updateIsEgoVehicle(bool egoVehicle){
		this.isEgoVehicle = egoVehicle;
	}


	private void updateSignals(float delta){

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
		else{
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


	public virtual void UpdateWheels(float delta, float yawRate = 0) { }

	public virtual void ChangeColor(Color color) { }




}
