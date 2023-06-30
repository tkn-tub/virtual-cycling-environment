
#define S_FUNCTION_NAME  Lateral_Control
#define S_FUNCTION_LEVEL 2

//Define input and out put numbers

#define num_input                     		12     //number of inputs
#define num_output                     		1     //number of outputs
#define num_Parameters                 		9     //number of Parameters


//define input index

#define x_CoG_Global_index                     	0  
#define y_CoG_Global_index                     	1 
#define v_CoG_index                           	2  
#define Slip_Angle_index                     	3  
#define Yaw_Angle_index                        	4 
#define Yaw_Rate_index                        	5 
#define x_Desired_index                       	6 
#define y_Desired_index                       	7 
#define Yaw_Desired_index                     	8 
#define Yaw_Rate_Desired_index                  9 
#define v_Desired_index                       	10 
#define a_Desired_index                       	11 



//define input Width

#define x_CoG_Global_Width                   	1 
#define y_CoG_Global_Width                     	1 
#define v_CoG_Width                           	1 
#define Slip_Angle_Width                        1 
#define Yaw_Angle_Width                        	1 
#define Yaw_Rate_Width                        	1 
#define x_Desired_Width                       	1 
#define y_Desired_Width                       	1 
#define Yaw_Desired_Width                     	1 
#define Yaw_Rate_Desired_Width                  1 
#define v_Desired_Width                       	1 
#define a_Desired_Width                       	1 

//define output index

#define Steering_Angle_index                          0  
 
//define output width
#define Steering_Angle_Width                    1  


//Parameters Index

#define Damping                                 0
#define Time_Constant                           1
#define q                                       2   // The Distance in logitudinal direction of the Virtual point
#define m_Vehicle                               3   // Vehicle mass
#define Jz_Vehicle                              4   // Vehicle mass moment of Inertia
#define Lv                                      5   // Front Wheel base Length
#define Lh                                      6   // Back Wheel base length
#define Cav                                     7   // Schraeglaufsteifigkeit Vorne  
#define Cah                                     8   // Schraeglaufsteifigkeit Hinten 


//Include simstructure

#include "simstruc.h"


static void mdlInitializeSizes(SimStruct *S)
{
    ssSetNumSFcnParams(S, num_Parameters);  /* Number of expected parameters */
    if (ssGetNumSFcnParams(S) != ssGetSFcnParamsCount(S)) {
        /* Return if number of expected != number of actual parameters */
        return;
    }

    ssSetNumContStates(S, 0);
    ssSetNumDiscStates(S, 0);

    if (!ssSetNumInputPorts(S, num_input)) return;
    
    ssSetInputPortWidth(S, x_CoG_Global_index , x_CoG_Global_Width );
    ssSetInputPortWidth(S, y_CoG_Global_index, y_CoG_Global_Width );
    ssSetInputPortWidth(S, v_CoG_index, v_CoG_Width );
    ssSetInputPortWidth(S, Slip_Angle_index, Slip_Angle_Width );
    ssSetInputPortWidth(S, Yaw_Angle_index, Yaw_Angle_Width );
    ssSetInputPortWidth(S, Yaw_Rate_index, Yaw_Rate_Width );
    ssSetInputPortWidth(S, x_Desired_index , x_Desired_Width );
    ssSetInputPortWidth(S, y_Desired_index , y_Desired_Width );
    ssSetInputPortWidth(S, Yaw_Desired_index, Yaw_Desired_Width );
    ssSetInputPortWidth(S, Yaw_Rate_Desired_index, Yaw_Rate_Desired_Width );
    ssSetInputPortWidth(S, v_Desired_index, v_Desired_Width );
    ssSetInputPortWidth(S, a_Desired_index, a_Desired_Width );
    
    
    ssSetInputPortRequiredContiguous(S, x_CoG_Global_index , true); 
    ssSetInputPortRequiredContiguous(S, y_CoG_Global_index, true);
    ssSetInputPortRequiredContiguous(S, v_CoG_index, true);
    ssSetInputPortRequiredContiguous(S, Slip_Angle_index, true);
    ssSetInputPortRequiredContiguous(S, Yaw_Angle_index, true); 
    ssSetInputPortRequiredContiguous(S, Yaw_Rate_index, true);
    ssSetInputPortRequiredContiguous(S, x_Desired_index , true);
    ssSetInputPortRequiredContiguous(S, y_Desired_index , true);
    ssSetInputPortRequiredContiguous(S, Yaw_Desired_index, true); 
    ssSetInputPortRequiredContiguous(S, Yaw_Rate_Desired_index, true);
    ssSetInputPortRequiredContiguous(S, v_Desired_index, true);
    ssSetInputPortRequiredContiguous(S, a_Desired_index, true);
    
       
    ssSetInputPortDirectFeedThrough(S, x_CoG_Global_index , 1);
    ssSetInputPortDirectFeedThrough(S, y_CoG_Global_index, 1);
    ssSetInputPortDirectFeedThrough(S, v_CoG_index, 1);
    ssSetInputPortDirectFeedThrough(S, Slip_Angle_index, 1);
    ssSetInputPortDirectFeedThrough(S, Yaw_Angle_index, 1);
    ssSetInputPortDirectFeedThrough(S, Yaw_Rate_index, 1);
    ssSetInputPortDirectFeedThrough(S, x_Desired_index , 1);
    ssSetInputPortDirectFeedThrough(S, y_Desired_index , 1);
    ssSetInputPortDirectFeedThrough(S, Yaw_Desired_index, 1);
    ssSetInputPortDirectFeedThrough(S, Yaw_Rate_Desired_index, 1);
    ssSetInputPortDirectFeedThrough(S, v_Desired_index, 1);
    ssSetInputPortDirectFeedThrough(S, a_Desired_index, 1);

    if (!ssSetNumOutputPorts(S, num_output)) return;
    ssSetOutputPortWidth(S, Steering_Angle_index, Steering_Angle_Width);
   

    
//leave it as it is
    ssSetNumSampleTimes(S, 1);
    ssSetNumRWork(S, 0);
    ssSetNumIWork(S, 0);
    ssSetNumPWork(S, 0);
    ssSetNumModes(S, 0);
    ssSetNumNonsampledZCs(S, 0);

    /* Specify the sim state compliance to be same as a built-in block */
    ssSetSimStateCompliance(S, USE_DEFAULT_SIM_STATE);

    ssSetOptions(S, 0);
}



/* Function: mdlInitializeSampleTimes =========================================
 * Abstract:
 *    This function is used to specify the sample time(s) for your
 *    S-function. You must register the same number of sample times as
 *    specified in ssSetNumSampleTimes.
 */
static void mdlInitializeSampleTimes(SimStruct *S)
{
    ssSetSampleTime(S, 0, CONTINUOUS_SAMPLE_TIME);
    ssSetOffsetTime(S, 0, 0.0);

}



#define MDL_INITIALIZE_CONDITIONS   /* Change to #undef to remove function */
#if defined(MDL_INITIALIZE_CONDITIONS)
  /* Function: mdlInitializeConditions ========================================
   * Abstract:
   *    In this function, you should initialize the continuous and discrete
   *    states for your S-function block.  The initial states are placed
   *    in the state vector, ssGetContStates(S) or ssGetRealDiscStates(S).
   *    You can also perform any other initialization activities that your
   *    S-function may require. Note, this routine will be called at the
   *    start of simulation and if it is present in an enabled subsystem
   *    configured to reset states, it will be call when the enabled subsystem
   *    restarts execution to reset the states.
   */
  static void mdlInitializeConditions(SimStruct *S)
  {
  }
#endif /* MDL_INITIALIZE_CONDITIONS */



#define MDL_START  /* Change to #undef to remove function */
#if defined(MDL_START) 
  /* Function: mdlStart =======================================================
   * Abstract:
   *    This function is called once at start of model execution. If you
   *    have states that should be initialized once, this is the place
   *    to do it.
   */
  static void mdlStart(SimStruct *S)
  {
          
  }
#endif /*  MDL_START */



/* Function: mdlOutputs =======================================================
 * Abstract:
 *    In this function, you compute the outputs of your S-function
 *    block.
 */
static void mdlOutputs(SimStruct *S, int_T tid)
{
     
    //get the adress of input data
    const real_T *Val_x_CoG_Global = (const real_T*) ssGetInputPortSignal(S,x_CoG_Global_index );
    const real_T *Val_y_CoG_Global = (const real_T*) ssGetInputPortSignal(S,y_CoG_Global_index);
    const real_T *Val_v_CoG =  (const real_T*) ssGetInputPortSignal(S,v_CoG_index);
    const real_T *Val_Slip_Angle = (const real_T*) ssGetInputPortSignal(S,Slip_Angle_index);
    const real_T *Val_Yaw_Angle  = (const real_T*) ssGetInputPortSignal(S,Yaw_Angle_index );
    const real_T *Val_Yaw_Rate =  (const real_T*) ssGetInputPortSignal(S,Yaw_Rate_index);
    const real_T *Val_x_Desired = (const real_T*) ssGetInputPortSignal(S,x_Desired_index );
    const real_T *Val_y_Desired = (const real_T*) ssGetInputPortSignal(S,y_Desired_index );
    const real_T *Val_Yaw_Desired =(const real_T*) ssGetInputPortSignal(S,Yaw_Desired_index);
    const real_T *Val_Yaw_Rate_Desired  = (const real_T*) ssGetInputPortSignal(S,Yaw_Rate_Desired_index );
    const real_T *Val_v_Desired  = (const real_T*) ssGetInputPortSignal(S,v_Desired_index );
    const real_T *Val_a_Desired = (const real_T*) ssGetInputPortSignal(S,a_Desired_index);
    
     //output the data to the port
    real_T       *Steering_Angle = ssGetOutputPortSignal(S,Steering_Angle_index);
    
    
    //declare needed Variables

//controller Parameters
real_T alpha_1;
real_T alpha_2;
real_T lamda;
//abbreviations
real_T si_psi;
real_T co_psi;
real_T si_delta;
real_T co_delta;
real_T  si_psi_Desired;
real_T  co_psi_Desired;
real_T sico1;
real_T sico2;
//Hinten Seitenkraft
real_T Sh;
//needed sub-Calculations
real_T x_pp;
real_T y_pp;
real_T Qn;
real_T Qz;
real_T Sv;
    //Parameters

// declare and save the Parameters in variables
           
const real_T       Para_D= mxGetPr(ssGetSFcnParam(S, Damping ))[0];
const real_T       Para_T= mxGetPr(ssGetSFcnParam(S, Time_Constant))[0];
const real_T       Para_q= mxGetPr(ssGetSFcnParam(S, q))[0];
const real_T       Para_m= mxGetPr(ssGetSFcnParam(S, m_Vehicle ))[0];
const real_T       Para_Jz= mxGetPr(ssGetSFcnParam(S, Jz_Vehicle))[0];
const real_T       Para_Lv= mxGetPr(ssGetSFcnParam(S,  Lv))[0];
const real_T       Para_Lh= mxGetPr(ssGetSFcnParam(S, Lh))[0];
const real_T       Para_Cav= mxGetPr(ssGetSFcnParam(S, Cav))[0];
const real_T       Para_Cah= mxGetPr(ssGetSFcnParam(S, Cah))[0]; 
   
    
    //Calculation Area
    //-------------------------------------------
    //calculation of controller's parameters 
    alpha_1=1/pow(Para_T,2);
    alpha_2=2*Para_D/Para_T;
    lamda=alpha_1;
    
    //needed abbreviations
    //angeles cos sin 
    si_psi=sin(Val_Yaw_Angle[0]);
    co_psi=cos(Val_Yaw_Angle[0]);
    si_delta=sin(Val_Yaw_Angle[0]-Val_Slip_Angle[0]);
    co_delta=cos(Val_Yaw_Angle[0]-Val_Slip_Angle[0]);
    si_psi_Desired=sin(Val_Yaw_Desired[0]);
    co_psi_Desired=cos(Val_Yaw_Desired[0]);    
    // Hinten Lateral Force
    Sh=((Para_Lh*Val_Yaw_Rate[0]/Val_v_CoG[0])+Val_Slip_Angle[0])*Para_Cah;
    // Xpp and Ypp
    x_pp=(lamda*Val_x_Desired[0]+alpha_2*Val_v_Desired[0]*co_psi_Desired+Val_a_Desired[0]*co_psi_Desired-Val_v_Desired[0]*si_psi_Desired*Val_Yaw_Rate_Desired[0]) - alpha_1*(Val_x_CoG_Global[0]+Para_q*co_psi) - alpha_2*(Val_v_CoG[0]*co_delta-Para_q*Val_Yaw_Rate[0]*si_psi);    
    y_pp=(lamda*Val_y_Desired[0]+alpha_2*Val_v_Desired[0]*si_psi_Desired+Val_a_Desired[0]*si_psi_Desired+Val_v_Desired[0]*co_psi_Desired*Val_Yaw_Rate_Desired[0]) - alpha_1*(Val_y_CoG_Global[0]+Para_q*si_psi) - alpha_2*(Val_v_CoG[0]*si_delta+Para_q*Val_Yaw_Rate[0]*co_psi);
    //sin cos compination that will be used more than one time
    sico1=si_psi*si_delta+co_psi*co_delta;   //plus
    sico2=co_psi*si_delta-si_psi*co_delta;   //minus
    
    Qn=(Para_q*Para_m*Para_Lv/Para_Jz) * (Val_Slip_Angle[0]*sico2-sico1);
    Qz=(Para_q*Para_m) * ( (sico1*(Val_Slip_Angle[0]*pow(Val_Yaw_Rate[0],2)-Para_Lh*Sh/Para_Jz)) + (sico2*(pow(Val_Yaw_Rate[0],2)+Para_Lh*Sh*Val_Slip_Angle[0]/Para_Jz)));
    
    Sv=(1/(1-Qn)) * (-Sh - Qz - Para_m*((Val_Slip_Angle[0]*co_delta+si_delta)*x_pp + (Val_Slip_Angle[0]*si_delta-co_delta)*y_pp)); //
    
    

   
    //send the out put to the output port
    Steering_Angle[0] =Sv/Para_Cav - Val_Slip_Angle[0] + Val_Yaw_Rate[0]*Para_Lv/Val_v_CoG[0];   
    
}



#define MDL_UPDATE  /* Change to #undef to remove function */
#if defined(MDL_UPDATE)
  /* Function: mdlUpdate ======================================================
   * Abstract:
   *    This function is called once for every major integration time step.
   *    Discrete states are typically updated here, but this function is useful
   *    for performing any tasks that should only take place once per
   *    integration step.
   */
  static void mdlUpdate(SimStruct *S, int_T tid)
  {
  }
#endif /* MDL_UPDATE */



#define MDL_DERIVATIVES  /* Change to #undef to remove function */
#if defined(MDL_DERIVATIVES)
  /* Function: mdlDerivatives =================================================
   * Abstract:
   *    In this function, you compute the S-function block's derivatives.
   *    The derivatives are placed in the derivative vector, ssGetdX(S).
   */
  static void mdlDerivatives(SimStruct *S)
  {
  }
#endif /* MDL_DERIVATIVES */



/* Function: mdlTerminate =====================================================
 * Abstract:
 *    In this function, you should perform any actions that are necessary
 *    at the termination of a simulation.  For example, if memory was
 *    allocated in mdlStart, this is the place to free it.
 */
static void mdlTerminate(SimStruct *S)
{
    
}


/*=============================*
 * Required S-function trailer *
 *=============================*/

#ifdef  MATLAB_MEX_FILE    /* Is this file being compiled as a MEX-file? */
#include "simulink.c"      /* MEX-file interface mechanism */
#else
#include "cg_sfun.h"       /* Code generation registration function */
#endif
