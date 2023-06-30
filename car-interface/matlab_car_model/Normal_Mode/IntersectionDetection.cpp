//#include <iostream>
//include for the intersection code


#define S_FUNCTION_LEVEL 2
#define S_FUNCTION_NAME  IntersectionDetection

#include <math.h>
//#include <stdio.h>

/*
 * Need to include simstruc.h for the definition of the SimStruct and
 * its associated macro definitions.
 */
#include "simstruc.h"
// #include "rtwintgt.h"
// #define IS_PARAM_DOUBLE(pVal) (mxIsNumeric(pVal) && !mxIsLogical(pVal) &&\
// !mxIsEmpty(pVal) && !mxIsSparse(pVal) && !mxIsComplex(pVal) && mxIsDouble(pVal))
//-----------------------------------------------------------------------

//Define input, output and parameter numbers
#define num_input                     		6     //number of inputs
#define num_output                     		1     //number of outputs
#define num_Parameters                 		2     //number of Parameters
#define num_Dwork                      		3     //number of Parameters

//define parameters index
#define num_Fellows_index             		0
#define filter_radius_index             	1
// parameters value
#define filter_radius             	        (int_T)mxGetPr(ssGetSFcnParam(S, filter_radius_index ))[0]

//define input index
#define Cuboid_Dimentions_index             0  
#define Tiangle_Upper_Points_index          1 
#define Tiangle_Center_Points_index         2 
#define Tiangle_Lower_Points_index          3 
#define Is_Fellows_inside_Filter_index      4
#define flag_new_round_index                5


//define input Width
#define Cuboid_Dimentions_width             (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]*3  
#define Tiangle_Upper_Points_width          (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]*9 
#define Tiangle_Center_Points_width         (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]*9
#define Tiangle_Lower_Points_width          (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]*9 
#define Is_Fellows_inside_Filter_width        (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]
#define flag_new_round_width                1


//define output index
#define Object_Detected_index               0  
 
//define output width
#define Object_Detected_width               (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]  

//define Dwork index
#define Dwork_Fellows_state_ini_index       0
#define Dwork_Fellows_state_index           1
#define Dwork_new_round_index               2

// define Dwork width
#define Dwork_Fellows_state_ini_width       (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]
#define Dwork_Fellows_state_width           (int_T)mxGetPr(ssGetSFcnParam(S, num_Fellows_index ))[0]
#define Dwork_new_round_width               1


// the code of intersection
#define X 0
#define Y 1
#define Z 2
#define CROSS(dest,v1,v2) \
          dest[0]=v1[1]*v2[2]-v1[2]*v2[1]; \
          dest[1]=v1[2]*v2[0]-v1[0]*v2[2]; \
          dest[2]=v1[0]*v2[1]-v1[1]*v2[0]; 
          
#define DOT(v1,v2) (v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2])
          
#define SUB(dest,v1,v2) \
          dest[0]=v1[0]-v2[0]; \
          dest[1]=v1[1]-v2[1]; \
          dest[2]=v1[2]-v2[2]; 
          
#define FINDMINMAX(x0,x1,x2,min,max) \
  min = max = x0;   \
  if(x1<min) min=x1;\
  if(x1>max) max=x1;\
  if(x2<min) min=x2;\
  if(x2>max) max=x2;
  
  //function planeBoxOverlap  
  int planeBoxOverlap(float normal[3], float vert[3], float maxbox[3])	// -NJMP-
{
  int q;
  float vmin[3],vmax[3],v;
  for(q=X;q<=Z;q++)
  {
    v=vert[q];					// -NJMP-
    if(normal[q]>0.0f)
    {
      vmin[q]=-maxbox[q] - v;	// -NJMP-
      vmax[q]= maxbox[q] - v;	// -NJMP-
    }
    else
    {
      vmin[q]= maxbox[q] - v;	// -NJMP-
      vmax[q]=-maxbox[q] - v;	// -NJMP-
    }
  }
  if(DOT(normal,vmin)>0.0f) return 0;	// -NJMP-
  if(DOT(normal,vmax)>=0.0f) return 1;	// -NJMP- 

  return 0;
}
  
/*======================== X-tests ========================*/
#define AXISTEST_X01(a, b, fa, fb)			   \
	p0 = a*v0[Y] - b*v0[Z];			       	   \
	p2 = a*v2[Y] - b*v2[Z];			       	   \
        if(p0<p2) {min=p0; max=p2;} else {min=p2; max=p0;} \
	rad = fa * boxhalfsize[Y] + fb * boxhalfsize[Z];   \
	if(min>rad || max<-rad) return 0;

#define AXISTEST_X2(a, b, fa, fb)			   \
	p0 = a*v0[Y] - b*v0[Z];			           \
	p1 = a*v1[Y] - b*v1[Z];			       	   \
        if(p0<p1) {min=p0; max=p1;} else {min=p1; max=p0;} \
	rad = fa * boxhalfsize[Y] + fb * boxhalfsize[Z];   \
	if(min>rad || max<-rad) return 0;

/*======================== Y-tests ========================*/

#define AXISTEST_Y02(a, b, fa, fb)			   \
	p0 = -a*v0[X] + b*v0[Z];		      	   \
	p2 = -a*v2[X] + b*v2[Z];	       	       	   \
        if(p0<p2) {min=p0; max=p2;} else {min=p2; max=p0;} \
	rad = fa * boxhalfsize[X] + fb * boxhalfsize[Z];   \
	if(min>rad || max<-rad) return 0;

#define AXISTEST_Y1(a, b, fa, fb)			   \
	p0 = -a*v0[X] + b*v0[Z];		      	   \
	p1 = -a*v1[X] + b*v1[Z];	     	       	   \
        if(p0<p1) {min=p0; max=p1;} else {min=p1; max=p0;} \
	rad = fa * boxhalfsize[X] + fb * boxhalfsize[Z];   \
	if(min>rad || max<-rad) return 0;

/*======================== Z-tests ========================*/
#define AXISTEST_Z12(a, b, fa, fb)			   \
	p1 = a*v1[X] - b*v1[Y];			           \
	p2 = a*v2[X] - b*v2[Y];			       	   \
        if(p2<p1) {min=p2; max=p1;} else {min=p1; max=p2;} \
	rad = fa * boxhalfsize[X] + fb * boxhalfsize[Y];   \
	if(min>rad || max<-rad) return 0;

#define AXISTEST_Z0(a, b, fa, fb)			   \
	p0 = a*v0[X] - b*v0[Y];				   \
	p1 = a*v1[X] - b*v1[Y];			           \
        if(p0<p1) {min=p0; max=p1;} else {min=p1; max=p0;} \
	rad = fa * boxhalfsize[X] + fb * boxhalfsize[Y];   \
	if(min>rad || max<-rad) return 0;
    
// the main function that could be used to examine the intersection
int triBoxOverlap(float boxcenter[3],float boxhalfsize[3],float triverts[3][3])
{

  /*    use separating axis theorem to test overlap between triangle and box */
  /*    need to test for overlap in these directions: */
  /*    1) the {x,y,z}-directions (actually, since we use the AABB of the triangle */
  /*       we do not even need to test these) */
  /*    2) normal of the triangle */
  /*    3) crossproduct(edge from tri, {x,y,z}-directin) */
  /*       this gives 3x3=9 more tests */
   float v0[3],v1[3],v2[3];
//   float axis[3];
   float min,max,p0,p1,p2,rad,fex,fey,fez;		// -NJMP- "d" local variable removed
   float normal[3],e0[3],e1[3],e2[3];
   /* This is the fastest branch on Sun */
   /* move everything so that the boxcenter is in (0,0,0) */
   SUB(v0,triverts[0],boxcenter);
   SUB(v1,triverts[1],boxcenter);
   SUB(v2,triverts[2],boxcenter);
   /* compute triangle edges */
   SUB(e0,v1,v0);      /* tri edge 0 */
   SUB(e1,v2,v1);      /* tri edge 1 */
   SUB(e2,v0,v2);      /* tri edge 2 */
   /* Bullet 3:  */
   /*  test the 9 tests first (this was faster) */
   fex = fabsf(e0[X]);
   fey = fabsf(e0[Y]);
   fez = fabsf(e0[Z]);
   
   AXISTEST_X01(e0[Z], e0[Y], fez, fey);
   AXISTEST_Y02(e0[Z], e0[X], fez, fex);
   AXISTEST_Z12(e0[Y], e0[X], fey, fex);
   
   fex = fabsf(e1[X]);
   fey = fabsf(e1[Y]);
   fez = fabsf(e1[Z]);
   
   AXISTEST_X01(e1[Z], e1[Y], fez, fey);
   AXISTEST_Y02(e1[Z], e1[X], fez, fex);
   AXISTEST_Z0(e1[Y], e1[X], fey, fex);
   
   fex = fabsf(e2[X]);
   fey = fabsf(e2[Y]);
   fez = fabsf(e2[Z]);

   AXISTEST_X2(e2[Z], e2[Y], fez, fey);
   AXISTEST_Y1(e2[Z], e2[X], fez, fex);
   AXISTEST_Z12(e2[Y], e2[X], fey, fex);

   /* Bullet 1: */
   /*  first test overlap in the {x,y,z}-directions */
   /*  find min, max of the triangle each direction, and test for overlap in */
   /*  that direction -- this is equivalent to testing a minimal AABB around */
   /*  the triangle against the AABB */

   /* test in X-direction */
   FINDMINMAX(v0[X],v1[X],v2[X],min,max);
   if(min>boxhalfsize[X] || max<-boxhalfsize[X]) return 0;

   /* test in Y-direction */
   FINDMINMAX(v0[Y],v1[Y],v2[Y],min,max);
   if(min>boxhalfsize[Y] || max<-boxhalfsize[Y]) return 0;

   /* test in Z-direction */
   FINDMINMAX(v0[Z],v1[Z],v2[Z],min,max);
   if(min>boxhalfsize[Z] || max<-boxhalfsize[Z]) return 0;

   /* Bullet 2: */
   /*  test if the box intersects the plane of the triangle */
   /*  compute plane equation of triangle: normal*x+d=0 */
   CROSS(normal,e0,e1);
   // -NJMP- (line removed here)
   if(!planeBoxOverlap(normal,v0,boxhalfsize)) return 0;	// -NJMP-

   return 1;   /* box and triangle overlaps */
}


//--------------------------------------------------------------------------
//--------------------------------------------------------------------------


/*====================*
 * S-function methods *
 *====================*/

/* Function: mdlInitializeSizes ===============================================
 * Abstract:
 *    The sizes information is used by Simulink to determine the S-function
 *    block's characteristics (number of inputs, outputs, states, etc.).
 */
static void mdlInitializeSizes(SimStruct *S)
{
    ssSetNumSFcnParams(S, num_Parameters);  /* Number of expected parameters */
    if (ssGetNumSFcnParams(S) != ssGetSFcnParamsCount(S)) {
        /* Return if number of expected != number of actual parameters */
        return;
    }
        
    ssSetNumContStates(S, 0);
    ssSetNumDiscStates(S, 0);
  
    
    // inputs declaration and testing
    if (!ssSetNumInputPorts(S, num_input)) return;
    if (!ssSetNumOutputPorts(S, num_output)) return;
    /* Set dimensions of input and output ports */
    
        //if(!ssSetInputPortDimensionInfo( S, Tiangle_Upper_Points_index, DYNAMIC_DIMENSION)) return;
      //  if(!ssSetInputPortDimensionInfo( S, Tiangle_Center_Points_index, DYNAMIC_DIMENSION)) return;
       // if(!ssSetInputPortDimensionInfo( S, Tiangle_Lower_Points_index, DYNAMIC_DIMENSION)) return;
    
    //pass input port width                  5

    ssSetInputPortWidth(S, Cuboid_Dimentions_index, Cuboid_Dimentions_width);
    ssSetInputPortWidth(S, Tiangle_Upper_Points_index, Tiangle_Upper_Points_width);
    ssSetInputPortWidth( S ,Tiangle_Center_Points_index, Tiangle_Center_Points_width);
    ssSetInputPortWidth( S ,Tiangle_Lower_Points_index, Tiangle_Lower_Points_width);
    ssSetInputPortWidth( S ,Is_Fellows_inside_Filter_index, Is_Fellows_inside_Filter_width);
    ssSetInputPortWidth( S ,flag_new_round_index, flag_new_round_width);
    
    //  contiguous inputs
    ssSetInputPortRequiredContiguous(S, Cuboid_Dimentions_index, true);
    ssSetInputPortRequiredContiguous(S, Tiangle_Upper_Points_index, true);
    ssSetInputPortRequiredContiguous( S ,Tiangle_Center_Points_index, true);
    ssSetInputPortRequiredContiguous( S ,Tiangle_Lower_Points_index, true);
    ssSetInputPortRequiredContiguous( S ,Is_Fellows_inside_Filter_index, true);
    ssSetInputPortRequiredContiguous( S ,flag_new_round_index, true);


    //feedthrough input
    ssSetInputPortDirectFeedThrough(S, Cuboid_Dimentions_index, 1);
    ssSetInputPortDirectFeedThrough(S, Tiangle_Upper_Points_index, 1);
    ssSetInputPortDirectFeedThrough(S, Tiangle_Center_Points_index, 1);
    ssSetInputPortDirectFeedThrough(S, Tiangle_Lower_Points_index, 1);
    ssSetInputPortDirectFeedThrough(S, Is_Fellows_inside_Filter_index, 1); 
    ssSetInputPortDirectFeedThrough(S, flag_new_round_index, 1);
    
    //output width
    ssSetOutputPortWidth(S,Object_Detected_index  ,Object_Detected_width );

    ssSetNumSampleTimes(S, 1);
    ssSetNumRWork(S, 0);
    ssSetNumIWork(S, 0);
    ssSetNumPWork(S, 0); // reserve element in the pointers vector
    ssSetNumModes(S, 0); // to store a C++ object
    ssSetNumNonsampledZCs(S, 0);

    ssSetSimStateCompliance(S, USE_DEFAULT_SIM_STATE);
   
    
    
    //for Dworks 
    
    ssSetNumDWork(S, num_Dwork);
    ssSetDWorkWidth(S, Dwork_Fellows_state_ini_index, Dwork_Fellows_state_ini_width);
    ssSetDWorkWidth(S, Dwork_Fellows_state_index , Dwork_Fellows_state_width);
    ssSetDWorkWidth(S, Dwork_new_round_index , Dwork_new_round_width);    
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
    //ssSetModelReferenceSampleTimeDefaultInheritance(S);
}

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
      // intialize Dwork
      real_T *A = (real_T*) ssGetDWork(S,Dwork_Fellows_state_ini_index);
      real_T *B = (real_T*) ssGetDWork(S,Dwork_Fellows_state_index);
      real_T *C = (real_T*) ssGetDWork(S,Dwork_new_round_index);
      for(int j=0;j<Dwork_Fellows_state_width;j++)
      {
          A[j]=0;
          B[j]=0;          
      }
      C[0]=0;
      
      
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
    const real_T  *Cuboid_Dimentions = (const real_T*) ssGetInputPortSignal(S,Cuboid_Dimentions_index );
    const real_T  *Tiangle_Upper_Points = (const real_T*) ssGetInputPortSignal(S,Tiangle_Upper_Points_index);
    const real_T  *Tiangle_Center_Points = (const real_T*) ssGetInputPortSignal(S,Tiangle_Center_Points_index);
    const real_T  *Tiangle_Lower_Points = (const real_T*) ssGetInputPortSignal(S,Tiangle_Lower_Points_index);
    const real_T  *Is_Fellows_inside_Filter = (const real_T*) ssGetInputPortSignal(S,Is_Fellows_inside_Filter_index);
    const real_T  *flag_new_round = (const real_T*) ssGetInputPortSignal(S,flag_new_round_index);
    //get the adress of output data
    real_T  *Object_Detected = ssGetOutputPortRealSignal(S,Object_Detected_index);  
    
     
    //get adress Dwork
    real_T  *Dwork_Fellows_state_ini= (real_T*) ssGetDWork(S, Dwork_Fellows_state_ini_index);
    real_T  *Dwork_Fellows_state= (real_T*) ssGetDWork(S, Dwork_Fellows_state_index);
    real_T  *Dwork_new_round= (real_T*) ssGetDWork(S, Dwork_new_round_index);
    
    //variables
    //int_T num_Triangles_Upper = ssGetInputPortWidth(S, Tiangle_Upper_Points_index)/10; 
    
                              //int_T* output_Array = new int[Object_Detected_width];
    int isIntersected,isIntersected_upper,isIntersected_center,isIntersected_lower;
    float boxcenter[3]={0,0,0};
    float boxhalfsize[3];
    float triverts_upper[3][3]; 
    float triverts_center[3][3]; 
    float triverts_lower[3][3]; 
    //initialize the output array
    //for(int i=0;i<Object_Detected_width;i++)
      //  output_Array[i]=0;    
    //get the inputs and put them in float matrix
    
    
    if(flag_new_round[0]>=18.5 && Dwork_new_round[0]==0)  
    {
        Dwork_new_round[0]=1;
        for(int j=0;j<Object_Detected_width;j++)
      {
          Dwork_Fellows_state[j]=Dwork_Fellows_state_ini[j];
          Dwork_Fellows_state_ini[j]=0;          
      }
        
    }
    else if(flag_new_round[0]<2 && Dwork_new_round[0]==1)
    {
        Dwork_new_round[0]=0;
    }   
    
    for(int j=0;j<Object_Detected_width;j++)
    {
        if(Is_Fellows_inside_Filter[j]==1)
        {
             
             
    for(int i=0;i<3;i++)
    {
        boxhalfsize[i]=(float)Cuboid_Dimentions[i+j*3];
    }
    for(int i=0;i<3;i++)
    {
        triverts_center[0][i]=(float)Tiangle_Center_Points[i+j*9];
        triverts_center[1][i]=(float)Tiangle_Center_Points[i+3+j*9];
        triverts_center[2][i]=(float)Tiangle_Center_Points[i+6+j*9];
    }    
    for(int i=0;i<3;i++)
    {
        triverts_upper[0][i]=(float)Tiangle_Upper_Points[i+j*9];
        triverts_upper[1][i]=(float)Tiangle_Upper_Points[i+3+j*9];
        triverts_upper[2][i]=(float)Tiangle_Upper_Points[i+6+j*9];
    }    
    for(int i=0;i<3;i++)
    {
        triverts_lower[0][i]=(float)Tiangle_Lower_Points[i+j*9];
        triverts_lower[1][i]=(float)Tiangle_Lower_Points[i+3+j*9];
        triverts_lower[2][i]=(float)Tiangle_Lower_Points[i+6+j*9];
    }    
    // ask if one of the triangles intersects with the cuboid
    isIntersected_upper=triBoxOverlap(boxcenter,boxhalfsize,triverts_upper);
    isIntersected_center=triBoxOverlap(boxcenter,boxhalfsize,triverts_center);
    isIntersected_lower=triBoxOverlap(boxcenter,boxhalfsize,triverts_lower);    
    isIntersected=isIntersected_upper||isIntersected_center||isIntersected_lower;  
    //output_Array[j]=isIntersected; //fill the output array 
    if(Dwork_Fellows_state_ini[j]==0)
    {
        Dwork_Fellows_state_ini[j]=isIntersected;
    }
              
        }        
        else
            Dwork_Fellows_state_ini[j]=0;
                           //   output_Array[j]=0;   
    }
    
    /*if(flag_new_round[0]==1&Dwork_new_round[0]==0)
        Dwork_new_round[0]=1;
    else
        Dwork_new_round[0]=0;
    */
        
    
    
    
    //pass the output array to the output port
    for(int i=0;i<Object_Detected_width;i++)
        Object_Detected[i]=Dwork_Fellows_state[i];
        //Object_Detected[i]=output_Array[i];   
    
    
    
    // free the memory of the dynamicaly allocated array
    
                    // delete [] output_Array; 
       
}                                                

#ifdef MATLAB_MEX_FILE
/* For now mdlG[S]etSimState are only supported in normal simulation */

/* Define to indicate that this S-Function has the mdlG[S]etSimState mothods */
#define MDL_SIM_STATE

/* Function: mdlGetSimState =====================================================
 * Abstract:
 *
 */
static mxArray* mdlGetSimState(SimStruct* S)
{    
    return 0;
}
/* Function: mdlGetSimState =====================================================
 * Abstract:
 *
 */
static void mdlSetSimState(SimStruct* S, const mxArray* ma)
{
    
}

#endif


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
 * required for dynamic input output port size *
 *=============================*/

// #if defined(MATLAB_MEX_FILE)
// #define MDL_SET_INPUT_PORT_DIMENSION_INFO
// static void mdlSetInputPortDimensionInfo(SimStruct *S,int_T port,const DimsInfo_T *dimsInfo)
// {   
//    // int_T outWidth = ssGetOutputPortWidth(S, Object_Detected_index);
//     if(!ssSetInputPortDimensionInfo(S, port, dimsInfo)) return;  
//     //if (outWidth == DYNAMICALLY_SIZED){
//    //     if(!ssSetOutputPortDimensionInfo(S, port, dimsInfo)) return;
//    // }
//    
// }
// # define MDL_SET_OUTPUT_PORT_DIMENSION_INFO
// static void mdlSetOutputPortDimensionInfo(SimStruct *S,int_T port,const DimsInfo_T *dimsInfo)
// {
//   // if(!ssSetOutputPortDimensionInfo(S, port, dimsInfo)) return;
// }
// # define MDL_SET_DEFAULT_PORT_DIMENSION_INFO
// static void mdlSetDefaultPortDimensionInfo(SimStruct *S)
// {    
//     //int_T outWidth = ssGetOutputPortWidth(S, 0);
//     /* Output dimensions are unknown. Set it to scalar. */
//        // if(!ssSetOutputPortMatrixDimensions(S, 0, 1, 1)) return;
//     /* Input port dimension must be unknown. Set it to scalar. */
//        if(!ssSetInputPortMatrixDimensions(S, Tiangle_Upper_Points_index, 1, 1)) return;
//       if(!ssSetInputPortMatrixDimensions(S, Tiangle_Center_Points_index, 1, 1)) return;
//       if(!ssSetInputPortMatrixDimensions(S, Tiangle_Lower_Points_index, 1, 1)) return;    
// }
// #endif

        
/*======================================================*
 * See sfuntmpl.doc for the optional S-function methods *
 *======================================================*/

/*=============================*
 * Required S-function trailer *
 *=============================*/

#ifdef  MATLAB_MEX_FILE    /* Is this file being compiled as a MEX-file? */
#include "simulink.c"      /* MEX-file interface mechanism */
#else
#include "cg_sfun.h"       /* Code generation registration function */

#endif

