
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%    Engine Block Parameters    %%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 

%%

%Contact_On definition:

Para.DT.Contact_On.v=2;
Para.DT.Contact_On.unit='unitless';
Para.DT.Contact_On.desc='it a cost. indicating that the contact switch is on so the engine is enabled';
Para.DT.Contact_On.author='A.Eid';

%Engine_Lowest_rpm definition:

Para.DT.Engine_Lowest_rpm.v=800;
Para.DT.Engine_Lowest_rpm.unit='rpm';
Para.DT.Engine_Lowest_rpm.desc='it a cost. indicating the minimum allowed rpm for the engine to rotate';
Para.DT.Engine_Lowest_rpm.author='A.Eid';

%Flywheel_Inertia definition:

Para.DT.Flywheel_Inertia.v=0.04;
Para.DT.Flywheel_Inertia.unit='kg.m2';
Para.DT.Flywheel_Inertia.desc='it a cost. indicating the value of the inertia of the flywheel attached to the engine crank shaft';
Para.DT.Flywheel_Inertia.author='A.Eid';

%Engine_Stall_rpm definition:

Para.DT.Engine_Stall_rpm.v=600;
Para.DT.Engine_Stall_rpm.unit='rpm';
Para.DT.Engine_Stall_rpm.desc='it a cost. indicating the stall rpm of the engine';
Para.DT.Engine_Stall_rpm.author='A.Eid';

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%    Clutch Block Parameters    %%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%

%Max_Clutch_Pedal_Position definition:

Para.DT.Max_Clutch_Pedal_Position.v=0.9;
Para.DT.Max_Clutch_Pedal_Position.unit='unitless';
Para.DT.Max_Clutch_Pedal_Position.desc='it a cost. indicating the maximum clutch pedal value which can be sensed';
Para.DT.Max_Clutch_Pedal_Position.author='A.Eid';

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%    GearBox Block Parameters    %%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%

%First_Gear_reduction_Ratio definition:

Para.DT.First_Gear_reduction_Ratio.v=3.75;
Para.DT.First_Gear_reduction_Ratio.unit='unitless';
Para.DT.First_Gear_reduction_Ratio.desc='it a cost. indicating the reduction ratio of the first gear';
Para.DT.First_Gear_reduction_Ratio.author='A.Eid';

%Second_Gear_reduction_Ratio definition:

Para.DT.Second_Gear_reduction_Ratio.v=2.23;
Para.DT.Second_Gear_reduction_Ratio.unit='unitless';
Para.DT.Second_Gear_reduction_Ratio.desc='it a cost. indicating the reduction ratio of the second gear';
Para.DT.Second_Gear_reduction_Ratio.author='A.Eid';

%Third_Gear_reduction_Ratio definition:

Para.DT.Third_Gear_reduction_Ratio.v=1.51;
Para.DT.Third_Gear_reduction_Ratio.unit='unitless';
Para.DT.Third_Gear_reduction_Ratio.desc='it a cost. indicating the reduction ratio of the third gear';
Para.DT.Third_Gear_reduction_Ratio.author='A.Eid';


%Forth_Gear_reduction_Ratio definition:

Para.DT.Forth_Gear_reduction_Ratio.v=1.13;
Para.DT.Forth_Gear_reduction_Ratio.unit='unitless';
Para.DT.Forth_Gear_reduction_Ratio.desc='it a cost. indicating the reduction ratio of the forth gear';
Para.DT.Forth_Gear_reduction_Ratio.author='A.Eid';

%Fifth_Gear_reduction_Ratio definition:

Para.DT.Fifth_Gear_reduction_Ratio.v=0.7;
Para.DT.Fifth_Gear_reduction_Ratio.unit='unitless';
Para.DT.Fifth_Gear_reduction_Ratio.desc='it a cost. indicating the reduction ratio of the fifth gear';
Para.DT.Fifth_Gear_reduction_Ratio.author='A.Eid';

%Reverse_Gear_reduction_Ratio definition:

Para.DT.Reverse_Gear_reduction_Ratio.v=-3;
Para.DT.Reverse_Gear_reduction_Ratio.unit='unitless';
Para.DT.Reverse_Gear_reduction_Ratio.desc='it a cost. indicating the reduction ratio of the reverse gear';
Para.DT.Reverse_Gear_reduction_Ratio.author='A.Eid';

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%    Differential Block Parameters    %%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%

%Sun_Gear_No_Teeth definition:

Para.DT.Sun_Gear_No_Teeth.v=12;
Para.DT.Sun_Gear_No_Teeth.unit='unitless';
Para.DT.Sun_Gear_No_Teeth.desc='it a cost. indicating the number of the sun gear teeth (which is a part of the trasmission shaft)';
Para.DT.Sun_Gear_No_Teeth.author='A.Mamdouh';

%Crown_Gear_No_Teeth definition:

Para.DT.Crown_Gear_No_Teeth.v=60;
Para.DT.Crown_Gear_No_Teeth.unit='unitless';
Para.DT.Crown_Gear_No_Teeth.desc='it a cost. indicating the number of the crown gear teeth (which is connected to the rear wheels)';
Para.DT.Crown_Gear_No_Teeth.author='A.Mamdouh';

Para.DT.Differential_Gear_ratio.v=4;
%%

%%%%%%%%%%%%%%%%%%%%%%%%%%
%      the shaft         %
%%%%%%%%%%%%%%%%%%%%%%%%%%

KS=17190;                    % the stiffness factor
DS= 600;                     % the damping factor
I_trans=30;                  % the inertia of the shaft

%%%%%%%%%%%%%%%%%%%%%%%%%%%
%      braking system     %
%%%%%%%%%%%%%%%%%%%%%%%%%%%
Para.DT.Torque_max_Brake.v=1500;

Kbf=13.33;                      %  constant for the fornt wheel
Kbr= 6.66;                      %  constant for the rear wheel
alpha_rear_wheel= .01;          % constant
Kc=1;                           % constant take as unity and its value lumped in kbf
                                % the front and the rear pressure gain
taw_s=.2;                       % delay time for the hydroulic system

inertia_wheel=4.5;              % the inrtia of the wheeel

cf_rear=.1;                     % viscous _friction_co_efficient 

cf_front=.1;                    % viscous _friction_co_efficient 

effictive_radius=.3;

% Engine_Map;















