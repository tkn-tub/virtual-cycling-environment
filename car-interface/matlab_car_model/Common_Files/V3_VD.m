

%% Vhicle Dynamics Constants %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


Para.VD.gravity.v=9.81;                                   %%gravity acceleration(m/sec^2)
Para.VD.gravity.unit='m/sec^2';
Para.VD.gravity.desc='Acceleration due to gravity';
Para.VD.gravity.author='VD Group';

Para.VD.Mass.v=1500;                                      %%center of gravity mass(kg)
Para.VD.Mass.unit='kg';
Para.VD.Mass.desc='Vehicle total mass';
Para.VD.Mass.author='VD Group';

Para.VD.Inertia_zz.v=3000;%2000;                                 %%Inertia about Z-axis(Nm^2)
Para.VD.Inertia_zz.unit='Nm^2';
Para.VD.Inertia_zz.desc='moment of inertia about Z-axis';
Para.VD.Inertia_zz.author='VD Group';


Para.VD.Inertia_xx.v=750;%500;                                 %%Inertia about x-axis(Nm^2)
Para.VD.Inertia_xx.unit='Nm^2';
Para.VD.Inertia_xx.desc='moment of inertia about x-axis';
Para.VD.Inertia_xx.author='VD Group';


Para.VD.Inertia_yy.v=3000;%2000;                                 %%Inertia about y-axis(Nm^2)
Para.VD.Inertia_yy.unit='Nm^2';
Para.VD.Inertia_yy.desc='moment of inertia about y-axis';
Para.VD.Inertia_yy.author='VD Group';

Para.VD.Length_Front.v=1.2;                               %%length from front wheel to center of gravity(m)
Para.VD.Length_Front.unit='m';
Para.VD.Length_Front.desc='Length from center of gravity to the front wheel position';
Para.VD.Length_Front.author='VD Group';

Para.VD.Length_Rear.v=1.5;                                %%length from rear wheel to center of gravity(m)
Para.VD.Length_Rear.unit='m';
Para.VD.Length_Rear.desc='Length from center of gravity to the front wheel position';
Para.VD.Length_Rear.author='VD Group';

Para.VD.Wheel_Base_Length.v=Para.VD.Length_Rear.v+Para.VD.Length_Front.v;     %%length of longtudinal wheel length(m)
Para.VD.Wheel_Base_Length.unit='m';
Para.VD.Wheel_Base_Length.desc='Length from front wheel position to rear wheel position';
Para.VD.Wheel_Base_Length.author='VD Group';

Para.VD.Wheel_Base_Width.v=1.5;                           %%Lateral distance btween wheels on the same axis(m)
Para.VD.Wheel_Base_Width.unit='m';
Para.VD.Wheel_Base_Width.desc='Width from Left wheel position to right wheel position';
Para.VD.Wheel_Base_Width.author='VD Group';

Para.VD.Minimum_Turning_Radius.v=10;                       %%minimum turning radius(m)
Para.VD.Minimum_Turning_Radius.unit='m';
Para.VD.Minimum_Turning_Radius.desc='Minimum Turning radius of the car at full steer range';
Para.VD.Minimum_Turning_Radius.author='VD Group';

Para.VD.Air_Risistance_Coefficient.v=0.4*3*1.2*0.5;                 %%air risistance coefficient(kg/m) 0.5*coof*A*rho
Para.VD.Air_Risistance_Coefficient.unit='kg/m';
Para.VD.Air_Risistance_Coefficient.desc='Air Risistance coefficient due to aero dynamics of the car design';
Para.VD.Air_Risistance_Coefficient.author='VD Group';


Para.VD.CG_Height.v=0.5;                                      %%center of gravity hight(m)
Para.VD.CG_Height.unit='m';
Para.VD.CG_Height.desc='intial heigth of the CG from the ground';
Para.VD.CG_Height.author='VD Group';

%----------------------------------------------------------------------
%Suspention System

Para.VD.Spring_Stifness_Front.v=28000;                               %%Suspention Spring Stifness (K)
Para.VD.Spring_Stifness.unit='N/m';
Para.VD.Spring_Stifness.desc='Suspention front Spring Stifness';
Para.VD.Spring_Stifness.author='VD Group';


Para.VD.Spring_Stifness_Rear.v=21000;                               %%Suspention Spring Stifness (K)
Para.VD.Spring_Stifness.unit='N/m';
Para.VD.Spring_Stifness.desc='Suspention rear Spring Stifness';
Para.VD.Spring_Stifness.author='VD Group';

Para.VD.Spring_Free_length.v=0.8;                               %suspention spring free length
Para.VD.Spring_Free_length.unit='m';
Para.VD.Spring_Free_length.desc='suspention spring free length';
Para.VD.Spring_Free_length.author='VD Group';


Para.VD.Spring_precompressed_length.v=0.3;                               %length diff for spring precompression
Para.VD.Spring_precompressed_length.unit='m';
Para.VD.Spring_precompressed_length.desc='length diff for spring precompression';
Para.VD.Spring_precompressed_length.author='VD Group';

%Para.VD.Damper_Damping_Constant.v=5000;                               %Damping Coeffecient of the damper


Para.VD.Damper_Damping_Constant_Front.v=2500;
Para.VD.Damper_Damping_Constant.unit='N/m/s';
Para.VD.Damper_Damping_Constant.desc='Damping Coeffecient of the front damper';
Para.VD.Damper_Damping_Constant.author='VD Group';

Para.VD.Damper_Damping_Constant_Rear.v=2000;
Para.VD.Damper_Damping_Constant.unit='N/m/s';
Para.VD.Damper_Damping_Constant.desc='Damping Coeffecient of the rear damper';
Para.VD.Damper_Damping_Constant.author='VD Group';

Para.VD.delta_z_max.v=1.2;                               %Maximum delta Z for the suspention system
Para.VD.delta_z_max.unit='m';
Para.VD.delta_z_max.desc='Maximum delta Z for the suspention system';
Para.VD.delta_z_max.author='VD Group';

Para.VD.delta_z_min.v=0.5;                               %Maximum delta Z for the suspention system
Para.VD.delta_z_min.unit='m';
Para.VD.delta_z_min.desc='Minimum delta Z for the suspention system';
Para.VD.delta_z_min.author='VD Group';

Para.VD.wheel_Mass.v=30;                                      %%unsprung mass(kg)
Para.VD.wheel_Mass.unit='kg';
Para.VD.wheel_Mass.desc='Mass of the unsprung mass';
Para.VD.wheel_Mass.author='VD Group';





Para.VD.Spring_intial_length.v=.5;                                      
Para.VD.Spring_intial_length.unit='m';
Para.VD.Spring_intial_length.desc='the intial length of the suspention systen at the start of the simulation';
Para.VD.Spring_intial_length.author='VD Group';

Para.VD.Spring_Lower_limit.v=.2;                                      
Para.VD.Spring_Lower_limit.unit='m';
Para.VD.Spring_Lower_limit.desc='the min length of the suspention systen';
Para.VD.Spring_Lower_limit.author='VD Group';

Para.VD.Spring_Upper_limit.v=.7;                                     
Para.VD.Spring_Upper_limit.unit='m';
Para.VD.Spring_Upper_limit.desc='the max length of the suspention systen';
Para.VD.Spring_Upper_limit.author='VD Group';




%******************************************vertical of tire

Para.VD.Tire_Stifness.v=2000;
Para.VD.Tire_Stifness.unit='N/m';
Para.VD.Tire_Stifness.desc='Spring Stifness of tire';
Para.VD.Tire_Stifness.author='VD Group';


Para.VD.Tire_Damping_Constant.v=20000;
Para.VD.Tire_Damping_Constant.unit='N/m/s';
Para.VD.Tire_Damping_Constant.desc='Damping Coeffecient of the tire';
Para.VD.Tire_Damping_Constant.author='VD Group';

Para.VD.Tire_radius.v=.3;
Para.VD.Tire_radius.unit='m';
Para.VD.Tire_radius.desc='Tire radius';
Para.VD.Tire_radius.author='VD Group';

Para.VD.Tire_Lower_limit.v=.2;                                      
Para.VD.Tire_Lower_limit.unit='m';
Para.VD.Tire_Lower_limit.desc='the min length of the suspention systen of the Tire';
Para.VD.Tire_Lower_limit.author='VD Group';

Para.VD.Tire_Upper_limit.v=Para.VD.Tire_radius.v;                                     
Para.VD.Tire_Upper_limit.unit='m';
Para.VD.Tire_Upper_limit.desc='the max length of the suspention systen of the Tire';
Para.VD.Tire_Upper_limit.author='VD Group';

Para.VD.Tire_intial_length.v=.25;                                      
Para.VD.Tire_intial_length.unit='m';
Para.VD.Tire_intial_length.desc='the intial length of the Tire at the start of the simulation';
Para.VD.Tire_intial_length.author='VD Group';

%%

Para.VD.Tire_wheel_inertia.v=3;                  %8.5 gives the best performance                     
Para.VD.Tire_wheel_inertia.unit='kgm^2';
Para.VD.Tire_wheel_inertia.desc='inertia of the wheel';
Para.VD.Tire_wheel_inertia.author='VD Group';


Para.VD.Wheels_viscous_friction.v=0.1;
Para.VD.Tire_wheel_inertia.unit='';
Para.VD.Tire_wheel_inertia.desc='viscous friction coeffecient';
Para.VD.Tire_wheel_inertia.author='VD Group';


%******************************************anti roll bar
Para.VD.AntiRoll_Stifness.v=0;                               
Para.VD.AntiRoll_Stifness.unit='N/m';
Para.VD.AntiRoll_Stifness.desc='anti roll Stifness   \|/______\|/ per relative dispalcement from rear wheels';
Para.VD.AntiRoll_Stifness.author='VD Group';



Para.VD.Suspention_Force_limt.v=inf;                               %%+-max force can be in Suspention 
Para.VD.Suspention_Force_limt.unit='N';
Para.VD.Suspention_Force_limt.desc='+-max force can be in Suspention';
Para.VD.Suspention_Force_limt.author='VD Group';


roadID = 1;
geometry_i = 1;
sprev = 0;
snew = 0;
currentLane = 0;
% x_points_msr=[];
% y_points_msr=[];
% [OpenDrive_tree, x_points,y_points] = Read_OpedDrive_File('sample1.1.xodr');
% [OpenDrive_tree, x_points,y_points] = Read_OpedDrive_File('Steckenborn_L747_plan_dSpace.xodr');

