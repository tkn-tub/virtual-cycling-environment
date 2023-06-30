using System;
using Godot;


public class BicycleRig : Spatial
{

	private Skeleton _skeleton;
	private KinematicBody _vehicle;
	private Transform _handleTransform;
//     // private Transform _frontWheelTransform;
//     // private Transform _rearWheelTransform;
	private Transform _pedalCrankset;
	private Transform _leftPedal;
	private Transform _rightPedal;
	private Transform _leftBrakeHandle, _frontBrakeBackLever, _frontBrakeFrontLever;
	private Transform _rightBrakeHandle, _rearBrakeBackLever, _rearBrakeFrontLever;


	private float _currentVelocity = 0f;

//     /*
//      Variables for the bicycle model as defined in these papers:
//      - Meijaard, J. P., Papadopoulos, J. M., Ruina, A., & Schwab, A. L. (2007, August). 
//      Linearized dynamics equations for the balance and steer of a bicycle: a benchmark and review. 
//      In Proceedings of the Royal Society of London A: Mathematical, Physical and Engineering Sciences 
//      (Vol. 463, No. 2084, pp. 1955-1982). The Royal Society.
//      - Schwab, A. L., & Recuero, A. M. (2013). 
//      Design and experimental validation of a haptic steering interface for the control input of a bicycle simulator. 
//      In Proceedings of ECCOMAS Multibody Dynamics Conference (pp. 1-4).
	 
//      For the lean angle, page 104 in the latter is especially useful.

	private float _steeringAngle = 0f;
	private Vector3 _rightVector = new Vector3();
	public Vector3 RightVector
	{
		get { return _rightVector; }
		set { _rightVector = value; }
	}
	private float _pedalDeltaRotation = 0f;


	/// <summary>
	/// Current velocity in m/s.
	/// </summary>
	public float CurrentVelocity
	{
		get { return _currentVelocity; }
		set { _currentVelocity = value; }
	}

	/// <summary>
	/// Current steering angle in degrees.
	/// </summary>
	public float SteeringAngle
	{
		get { return _steeringAngle; }
		set { _steeringAngle = value; }
	}

	// Bicycle object skeleton
	public Skeleton Skeleton
	{
		get { return _skeleton; }
		set { _skeleton = value; }
	}


	public override void _Ready()
	{
		// Ge required bicycle parts from skeleton
		_skeleton = this.GetNode<Skeleton>("Bicycle CCS Armature/Skeleton");

		_handleTransform = _skeleton.GetBonePose(_skeleton.FindBone("Handle"));
		_pedalCrankset =  _skeleton.GetBonePose(_skeleton.FindBone("PedalCrankset")); 
		_leftPedal =_skeleton.GetBonePose(_skeleton.FindBone("LeftPedal"));
		_rightPedal = _skeleton.GetBonePose(_skeleton.FindBone("RightPedal"));
		_leftBrakeHandle = _skeleton.GetBonePose(_skeleton.FindBone("LeftBrakeHandle"));
		_rightBrakeHandle = _skeleton.GetBonePose(_skeleton.FindBone("RightBrakeHandle"));
	}

		// Called every frame. 'delta' is the elapsed time since the previous frame.
	public override void _Process(float delta)
	{

		// Rotate handle
		Vector3 y_axis = new Vector3(0, 1, 0);
		_handleTransform = _handleTransform.Rotated(y_axis, _steeringAngle);
		_skeleton.SetBonePose(_skeleton.FindBone("Handle"), _handleTransform);

		// Turn the pedals based on current bicycle speed in the simulation
		Vector3 right_vector = new Vector3(0, 1,0);
		_pedalDeltaRotation = 2.0f * _currentVelocity * delta;
		_pedalCrankset = _pedalCrankset.Rotated(right_vector, -_pedalDeltaRotation);
		_skeleton.SetBonePose(_skeleton.FindBone("PedalCrankset"), _pedalCrankset);
	}


//     /// <summary>
//     /// Apply all transformations according to speed, braking, and steering.
//     /// This is not the Unity Update method! Must be called manually!
//     /// Also note that this will currently not alter the location or orientation of the bicycle.
//     /// </summary>
	public void Update(float delta)
	{
	   
	}

	/**
		 * Just for testing!
		 * TODO: Use a physically accurate bicycle dynamics model
		 */
	// public float GetLeanAngle()
	// {
	//     return _steeringAngle * -.2f;
	// }
	public Vector3 GetForwardVector()
	{
		return GetRotationVector(Rotation);
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

