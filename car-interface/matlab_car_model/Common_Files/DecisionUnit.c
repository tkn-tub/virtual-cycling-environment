
#define S_FUNCTION_NAME  DecisionUnit
#define S_FUNCTION_LEVEL 2

//Define input and out put numbers

#define num_input                           		13     //number of inputs
#define num_output                     	        	12     //number of outputs
#define num_Parameters                      		0     //number of Parameters
#define num_Dwork                      		        4     //number of Parameters


//define input index

#define active_system_index                     	0  
#define user_set_speed_index                     	1 
#define time_gap_user_index                         2  
#define object_in_lane_index                     	3  
#define distance_2_object_index                     4 
#define relative_velocity_index                     5 
#define T_current_index                             6
#define Braking_Distance_index                      7
#define delta_T_direction_index                     8
#define lateral_Distance_available_index            9
#define heading_angle_diff_index                   10
#define sim_time_index                             11
#define velocity_VUT_index                         12



//define input Width

#define active_system_width                     	1 
#define user_set_speed_width                     	1 
#define time_gap_user_width                         1 
#define object_in_lane_width                        1 
#define distance_2_object_width                    	1 
#define relative_velocity_width                    	1 
#define T_current_width                         	1 
#define Braking_Distance_width                      1
#define delta_T_direction_width                     1
#define lateral_Distance_available_width            1
#define heading_angle_diff_width                    1
#define sim_time_width                              1
#define velocity_VUT_width                          1

//define output index

#define enable_longitudinal_index                   0 
#define enable_lateral_index                        1 
#define velocity_desired_index                      2  
#define object_detected_index                       3 
#define distance_index                              4 
#define v_relative_index                            5 
#define time_gap_index                              6 
#define t_desired_index                             7 
#define lateral_velocity_max_index                  8
#define Switch_a_or_v_control_index                 9
#define a_desired_index                             10
#define danger_front_index                          11
 
//define output width
#define enable_longitudinal_width                   1 
#define enable_lateral_width                        1 
#define velocity_desired_width                      1  
#define object_detected_width                       1 
#define distance_width                              1 
#define v_relative_width                            1 
#define time_gap_width                              1 
#define t_desired_width                             1 
#define lateral_velocity_max_width                  1
#define Switch_a_or_v_control_width                 1 
#define a_desired_width                             1
#define danger_front_width                          1


//define Dwork index
#define Dwork_T_desired_index                       0
#define Dwork_EBS_Flag_index                        1
#define Dwork_sim_time_index                        2
#define Dwork_ESS_Flag_index                        3





//Include simstructure

#include "simstruc.h"
// int sign(real_T val)
// {
//     if(val<0)
//         return -1;
//     else if(val>0)
//         return 1;
//     else
//         return 0;
// }

real_T  degreeOfDanger(real_T v_vehicle,real_T v_rel,real_T dist,real_T object_detected, real_T braking_dist )
{
    int S1=(pow(v_rel,2)/3.5)+(v_vehicle*2.3)+4;
//     int S2=(-pow(v_rel,2)*sign(v_rel)/8)+(v_vehicle*2.3)+4;
    if (object_detected==1 &&v_rel>0 )
        return 1;
    else if (object_detected==1 &&dist>S1 )
        return 1;
    else if (object_detected==1 &&dist<=S1 &&dist>(braking_dist*1.5) )
         return 2;
    else if (object_detected==1 &&dist<=(braking_dist*1.5) )
         return 3;
    else
         return 1;
}
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
    
    ssSetInputPortWidth(S, active_system_index , active_system_width );
    ssSetInputPortWidth(S, user_set_speed_index, user_set_speed_width );
    ssSetInputPortWidth(S,time_gap_user_index, time_gap_user_width );
    ssSetInputPortWidth(S, object_in_lane_index, object_in_lane_width );
    ssSetInputPortWidth(S, distance_2_object_index, distance_2_object_width );
    ssSetInputPortWidth(S, relative_velocity_index, relative_velocity_width );    
    ssSetInputPortWidth(S, T_current_index, T_current_width );  
    ssSetInputPortWidth(S, Braking_Distance_index, Braking_Distance_width );
    ssSetInputPortWidth(S, delta_T_direction_index, delta_T_direction_width );
    ssSetInputPortWidth(S, lateral_Distance_available_index, lateral_Distance_available_width );
    ssSetInputPortWidth(S, heading_angle_diff_index, heading_angle_diff_width );
    ssSetInputPortWidth(S, sim_time_index, sim_time_width );
    ssSetInputPortWidth(S, velocity_VUT_index, velocity_VUT_width );
    
    
    ssSetInputPortRequiredContiguous(S, active_system_index , true); 
    ssSetInputPortRequiredContiguous(S, user_set_speed_index, true);
    ssSetInputPortRequiredContiguous(S, time_gap_user_index, true);
    ssSetInputPortRequiredContiguous(S, object_in_lane_index, true);
    ssSetInputPortRequiredContiguous(S, distance_2_object_index, true); 
    ssSetInputPortRequiredContiguous(S, relative_velocity_index, true);
    ssSetInputPortRequiredContiguous(S, T_current_index, true);
    ssSetInputPortRequiredContiguous(S, Braking_Distance_index, true);
    ssSetInputPortRequiredContiguous(S, delta_T_direction_index, true);
    ssSetInputPortRequiredContiguous(S, lateral_Distance_available_index, true);
    ssSetInputPortRequiredContiguous(S, heading_angle_diff_index, true);
    ssSetInputPortRequiredContiguous(S, sim_time_index, true);
    ssSetInputPortRequiredContiguous(S, velocity_VUT_index, true);
    
       
    ssSetInputPortDirectFeedThrough(S, active_system_index , 1);
    ssSetInputPortDirectFeedThrough(S, user_set_speed_index, 1);
    ssSetInputPortDirectFeedThrough(S, time_gap_user_index, 1);
    ssSetInputPortDirectFeedThrough(S, object_in_lane_index, 1);
    ssSetInputPortDirectFeedThrough(S, distance_2_object_index, 1);
    ssSetInputPortDirectFeedThrough(S, relative_velocity_index, 1);
    ssSetInputPortDirectFeedThrough(S, T_current_index, 1);
    ssSetInputPortDirectFeedThrough(S, Braking_Distance_index, 1);
    ssSetInputPortDirectFeedThrough(S, delta_T_direction_index, 1);
    ssSetInputPortDirectFeedThrough(S, lateral_Distance_available_index, 1);
    ssSetInputPortDirectFeedThrough(S, heading_angle_diff_index, 1);
    ssSetInputPortDirectFeedThrough(S, sim_time_index, 1);
    ssSetInputPortDirectFeedThrough(S, velocity_VUT_index, 1);
    

    if (!ssSetNumOutputPorts(S, num_output)) return;
    
    ssSetOutputPortWidth(S, enable_longitudinal_index, enable_longitudinal_width );
    ssSetOutputPortWidth(S, enable_lateral_index , enable_lateral_width);
    ssSetOutputPortWidth(S, velocity_desired_index, velocity_desired_width );
    ssSetOutputPortWidth(S, object_detected_index, object_detected_width);
    ssSetOutputPortWidth(S, distance_index, distance_width );
    ssSetOutputPortWidth(S, v_relative_index, v_relative_width);
    ssSetOutputPortWidth(S, time_gap_index, time_gap_width);
    ssSetOutputPortWidth(S, t_desired_index, t_desired_width);
    ssSetOutputPortWidth(S, lateral_velocity_max_index, lateral_velocity_max_width);  
    ssSetOutputPortWidth(S, Switch_a_or_v_control_index, Switch_a_or_v_control_width);
    ssSetOutputPortWidth(S, a_desired_index, a_desired_width);
    ssSetOutputPortWidth(S, danger_front_index, danger_front_width);
   

    
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
    
    ssSetNumDWork(S, num_Dwork);
    ssSetDWorkWidth(S, Dwork_T_desired_index, 1);
    ssSetDWorkWidth(S, Dwork_EBS_Flag_index , 1);
    ssSetDWorkWidth(S, Dwork_ESS_Flag_index , 1);
    ssSetDWorkWidth(S, Dwork_sim_time_index , 1);
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
      real_T *T_ini = (real_T*) ssGetDWork(S,Dwork_T_desired_index);
      real_T *flag_ini1 = (real_T*) ssGetDWork(S,Dwork_EBS_Flag_index);
      real_T *flag_ini2 = (real_T*) ssGetDWork(S,Dwork_ESS_Flag_index);
      real_T *DW_sim_t_ini = (real_T*) ssGetDWork(S,Dwork_sim_time_index);

    /*  Initialize the  DWork  */
    T_ini[0] = -100;
    flag_ini1[0] = 0;
    flag_ini2[0] = 0;
    DW_sim_t_ini[0]=-1;
          
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
    const real_T *active_system = (const real_T*) ssGetInputPortSignal(S,active_system_index );
    const real_T *user_set_speed = (const real_T*) ssGetInputPortSignal(S,user_set_speed_index);
    const real_T *time_gap_user =  (const real_T*) ssGetInputPortSignal(S,time_gap_user_index);
    const real_T *object_in_lane = (const real_T*) ssGetInputPortSignal(S,object_in_lane_index);
    const real_T *distance_2_object  = (const real_T*) ssGetInputPortSignal(S,distance_2_object_index );
    const real_T *relative_velocity =  (const real_T*) ssGetInputPortSignal(S,relative_velocity_index);    
    const real_T *T_current =  (const real_T*) ssGetInputPortSignal(S,T_current_index);
    const real_T *Braking_Distance =  (const real_T*) ssGetInputPortSignal(S,Braking_Distance_index);
    const real_T *delta_T_direction =  (const real_T*) ssGetInputPortSignal(S,delta_T_direction_index);
    const real_T *lateral_Distance_available =  (const real_T*) ssGetInputPortSignal(S,lateral_Distance_available_index);
    const real_T *heading_angle_diff =  (const real_T*) ssGetInputPortSignal(S,heading_angle_diff_index);
    const real_T *sim_time =  (const real_T*) ssGetInputPortSignal(S,sim_time_index);
    const real_T *velocity_VUT =  (const real_T*) ssGetInputPortSignal(S,velocity_VUT_index);
    
    //Dwork
    real_T  *Dwork_T_desired= (real_T*) ssGetDWork(S, Dwork_T_desired_index);
    real_T  *Dwork_EBS_Flag= (real_T*) ssGetDWork(S, Dwork_EBS_Flag_index);
    real_T  *Dwork_sim_time= (real_T*) ssGetDWork(S, Dwork_sim_time_index);
    real_T  *Dwork_ESS_Flag= (real_T*) ssGetDWork(S, Dwork_ESS_Flag_index);
    
     //output the data to the port
    real_T       *enable_longitudinal = ssGetOutputPortSignal(S,enable_longitudinal_index);
    real_T       *enable_lateral = ssGetOutputPortSignal(S,enable_lateral_index);
    real_T       *velocity_desired = ssGetOutputPortSignal(S,velocity_desired_index);
    real_T       *object_detected = ssGetOutputPortSignal(S,object_detected_index);
    real_T       *distance = ssGetOutputPortSignal(S,distance_index);
    real_T       *v_relative = ssGetOutputPortSignal(S,v_relative_index);
    real_T       *time_gap = ssGetOutputPortSignal(S,time_gap_index);
    real_T       *t_desired = ssGetOutputPortSignal(S,t_desired_index);
    real_T       *lateral_velocity_max = ssGetOutputPortSignal(S,lateral_velocity_max_index);
    real_T       *Switch_a_or_v_control = ssGetOutputPortSignal(S,Switch_a_or_v_control_index); 
    real_T       *a_desired = ssGetOutputPortSignal(S,a_desired_index);
    real_T       *danger_front = ssGetOutputPortSignal(S,danger_front_index);
    
    
    //declare needed Variables 
    double array_output[11]={0,0,0,0,0,0,0,0,1000000,0,0};
    double degree_of_danger=0;
    //double array_default[11]={0};
    
    
switch ((int)active_system[0])
{
    case 1:
    array_output[0] =1;   
    array_output[1] =0;   
    array_output[2] =user_set_speed[0];   
    array_output[3] =object_in_lane[0];   
    array_output[4] =distance_2_object[0];   
    array_output[5] =relative_velocity[0];   
    array_output[6] =time_gap_user[0];   
    array_output[7] =0;   
    array_output[8] =1000000; 
    array_output[9] =1;
    array_output[10] =0;
    Dwork_T_desired[0]=-100;       //keep this line in every system rather than the second one to reset the memory for the next use of case 2
    degree_of_danger=degreeOfDanger(velocity_VUT[0],relative_velocity[0],distance_2_object[0],object_in_lane[0],Braking_Distance[0] );
    break;
    case 2:
        array_output[0] =1;
        array_output[1] =1;
        array_output[2] =60/3.6;
        array_output[3] =object_in_lane[0];
        array_output[4] =distance_2_object[0]; 
        array_output[5] =relative_velocity[0];
        array_output[6] =time_gap_user[0];
        if(Dwork_T_desired[0]==-100)
            Dwork_T_desired[0]=T_current[0];
        array_output[7] =Dwork_T_desired[0];   
        array_output[8] =1;
        array_output[9] =1;
        array_output[10] =0;    
        degree_of_danger=degreeOfDanger(velocity_VUT[0],relative_velocity[0],distance_2_object[0],object_in_lane[0],Braking_Distance[0] );
        break;
    case 3:
        if(distance_2_object[0]<Braking_Distance[0] && Dwork_EBS_Flag[0]==0)
            Dwork_EBS_Flag[0]=1;
//         if((distance_2_object[0]>1.5*Braking_Distance[0] && Dwork_EBS_Flag[0]==1 && relative_velocity[0]>=-0.1)|| object_in_lane[0]==0)
        if((distance_2_object[0]>1.5*Braking_Distance[0] &&Dwork_EBS_Flag[0]==1 && relative_velocity[0]>=-0.1)|| object_in_lane[0]==0)
            Dwork_EBS_Flag[0]=0;
        
        
        if(Dwork_EBS_Flag[0])
        {
            array_output[0] =1;   
            array_output[1] =0;   
            array_output[2] =0;   
            array_output[3] =0;   
            array_output[4] =0;   
            array_output[5] =0;   
            array_output[6] =0;   
            array_output[7] =0;   
            array_output[8] =1000000; 
            array_output[9] =0;
            array_output[10] =-10;
            
        }        
        Dwork_T_desired[0]=-100;      //keep this line in every system to reset the memory for the next use of case 2  
        degree_of_danger=degreeOfDanger(velocity_VUT[0],relative_velocity[0],distance_2_object[0],object_in_lane[0],Braking_Distance[0] );
        break;
    case 4:
        //in case of braking 
        if(distance_2_object[0]<=Braking_Distance[0] && Dwork_EBS_Flag[0]==0 && Dwork_ESS_Flag[0]==0)
            Dwork_EBS_Flag[0]=1;
         if((distance_2_object[0]>1.5*Braking_Distance[0] &&Dwork_EBS_Flag[0]==1 && relative_velocity[0]>=-0.1)|| object_in_lane[0]==0||distance_2_object[0]>3*Braking_Distance[0])
            Dwork_EBS_Flag[0]=0;
        //in case of steering 
        
         if((distance_2_object[0]>Braking_Distance[0]||object_in_lane[0]==0)&& Dwork_ESS_Flag[0]==1 &&abs(T_current[0]-Dwork_T_desired[0])<0.01 && heading_angle_diff[0]<0.1 && Dwork_sim_time[0]==-1)
                    Dwork_sim_time[0]=sim_time[0];    
        if(Dwork_sim_time[0]!=-1 && (sim_time[0]-Dwork_sim_time[0])>=1)
        {            
            Dwork_ESS_Flag[0]=0;
            Dwork_T_desired[0]=-100;
        }
     // execution
        if(Dwork_EBS_Flag[0])
        {
            if(distance_2_object[0]<(0.8*Braking_Distance[0]) && delta_T_direction[0]!=0  && Dwork_ESS_Flag[0]==0 && velocity_VUT[0]>11)
            {
                    Dwork_ESS_Flag[0]=1;
                    Dwork_EBS_Flag[0]=0;
                    break;
            }
            array_output[0] =1;   
            array_output[1] =0;   
            array_output[2] =0;   
            array_output[3] =0;   
            array_output[4] =0;   
            array_output[5] =0;   
            array_output[6] =0;   
            array_output[7] =0;   
            array_output[8] =1000000; 
            array_output[9] =0;
            array_output[10] =-10;                          
        }     
        
           
            else if(Dwork_ESS_Flag[0])
        {
            if(Dwork_T_desired[0]==-100)
                    Dwork_T_desired[0]=lateral_Distance_available[0]+T_current[0]+(1.2*delta_T_direction[0]);
            if(Dwork_T_desired[0]!=-100 &&distance_2_object[0]<Braking_Distance[0] && object_in_lane[0]==1 && delta_T_direction[0]!=0 &&Dwork_T_desired[0]!=(lateral_Distance_available[0]+T_current[0]+(1*delta_T_direction[0])))     
                     Dwork_T_desired[0]=lateral_Distance_available[0]+T_current[0]+(1*delta_T_direction[0]);            
            array_output[0] =0;   
            array_output[1] =1;   
            array_output[2] =0;   
            array_output[3] =0;   
            array_output[4] =0;   
            array_output[5] =0;   
            array_output[6] =0;   
            array_output[7] =Dwork_T_desired[0];   
            array_output[8] =2; 
            array_output[9] =0;
            array_output[10] =0;    
            if(Dwork_T_desired[0]!=-100 && delta_T_direction[0]==0 &&distance_2_object[0]<Braking_Distance[0] && object_in_lane[0]==1)
            {
                array_output[0] =1;
                array_output[9] =0;
                array_output[10] =-10;                     
            }
        }          
        else
        {
//             array_output[0] =1;   
//             array_output[1] =1;   
//             array_output[2] =60/3.6;   
//             array_output[3] =0;   
//             array_output[4] =0;   
//             array_output[5] =0;   
//             array_output[6] =0;   
//             array_output[7] =-5.4;    
//             array_output[8] =1;
//             array_output[9] =1;
//             array_output[10] =0;    
//             Dwork_sim_time[0]=-1;      
            
            
            array_output[0] =0;   
            array_output[1] =0;   
            array_output[2] =0;   
            array_output[3] =0;   
            array_output[4] =0;   
            array_output[5] =0;   
            array_output[6] =0;   
            array_output[7] =0;   
            array_output[8] =100000;          
            array_output[9] =1;
            array_output[10] =0;    
            Dwork_sim_time[0]=-1;     
        }    
        degree_of_danger=degreeOfDanger(velocity_VUT[0],relative_velocity[0],distance_2_object[0],object_in_lane[0],Braking_Distance[0] );
               
        break;
    default:
        Dwork_T_desired[0]=-100;
        Dwork_EBS_Flag[0]=0;
        Dwork_ESS_Flag[0]=0;
        Dwork_sim_time[0]=-1;
        break;  
        
}
   
    
    
//     pass the out put to the output port
    enable_longitudinal[0] =array_output[0];   
    enable_lateral[0] =array_output[1];   
    velocity_desired[0] =array_output[2];   
    object_detected[0] =array_output[3];   
    distance[0] =array_output[4];   
    v_relative[0] =array_output[5];   
    time_gap[0] =array_output[6];   
    t_desired[0] =array_output[7];   
    lateral_velocity_max[0] =array_output[8];
    Switch_a_or_v_control[0] =array_output[9];
    a_desired[0] =array_output[10];
    danger_front[0]=degree_of_danger;
     
    
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
