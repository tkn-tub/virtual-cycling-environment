%%
%acceleration Control

ADAS.Acceleration_Control.Throttel_PI.Kp=0.05;    %the P gain for the PI controller of the throttel control in the acceleration control
ADAS.Acceleration_Control.Throttel_PI.Ki=0.5;     %the I gain for the PI controller of the throttel control in the acceleration control
ADAS.Acceleration_Control.Throttel_PI.Kb=2;
ADAS.Acceleration_Control.Brake_PI.Kp=-0.05;      %the P gain for the PI controller of the Brake control in the acceleration control
ADAS.Acceleration_Control.Brake_PI.Ki=-0.5;       %the I gain for the PI controller of the Brake control in the acceleration control
ADAS.Acceleration_Control.Brake_PI.Kb=-1; 

%%
%velocity Control

ADAS.Velocity_Control.Kp=1;
ADAS.Velocity_Control.Ki=0.2;
ADAS.Velocity_Control.Kb=1;
ADAS.Velocity_Control.a_max=2;
ADAS.Velocity_Control.a_min=-3.5;

%%
%LAteral Controller

 ADAS.Lateral_Control.C_av=100000;
 ADAS.Lateral_Control.C_ah=160000;
 %ADAS.Lateral_Control.q=1; 
 ADAS.Lateral_Control.q=1;
 ADAS.Lateral_Control.time_constant=0.2;
 ADAS.Lateral_Control.Damping=1; 
 ADAS.Lateral_Control.delta_s=2; %Vorausschaudistanz
 

 
 %%
 %SENSORS
 % Fellow Vehicles
% para_num_fellow=5;
ADAS.Num_Fellows=10;
 Fellow_size=zeros(ADAS.Num_Fellows,3);
for i=1:ADAS.Num_Fellows
    Fellow_size(i,:)=[Para.VD.Length_Front.v  Para.VD.Wheel_Base_Width.v/2  0.7];
%     Fellow_size(i,:)=[4.7748/2  1.754/2  0.7];
end
ADAS.Front_Long_Range_Radar.Fellow_size=reshape(Fellow_size.',1,[])';

% L=Para.VD.Length_Front.v;
% W=Para.VD.Wheel_Base_Width.v/2;
% H=0.7;
% ADAS.Fellow_8_Points.FLU=[ L ;  W  ;   H];
% ADAS.Fellow_8_Points.FLL=[ L ;  W  ;  -H];
% ADAS.Fellow_8_Points.FRU=[ L ; -W  ;   H];
% ADAS.Fellow_8_Points.FRL=[ L ; -W  ;  -H];
% ADAS.Fellow_8_Points.RLU=[-L ;  W  ;   H];
% ADAS.Fellow_8_Points.RLL=[-L ;  W  ;  -H];
% ADAS.Fellow_8_Points.RRU=[-L ; -W  ;   H];
% ADAS.Fellow_8_Points.RRL=[-L ; -W  ;  -H];
% para_Fellow_8_Points=ADAS.Fellow_8_Points;
% 
% clear L W H;

Lv=1.8365;
Lh=Lv*1.6;
W=1.754/2;
Hu=0.7;
Hl=0.5;
ADAS.Fellow_8_Points.FLU=[ Lv ;  W  ;   Hu];
ADAS.Fellow_8_Points.FLL=[ Lv ;  W  ;  -Hl];
ADAS.Fellow_8_Points.FRU=[ Lv ; -W  ;   Hu];
ADAS.Fellow_8_Points.FRL=[ Lv ; -W  ;  -Hl];
ADAS.Fellow_8_Points.RLU=[-Lh ;  W  ;   Hu];
ADAS.Fellow_8_Points.RLL=[-Lh ;  W  ;  -Hl];
ADAS.Fellow_8_Points.RRU=[-Lh ; -W  ;   Hu];
ADAS.Fellow_8_Points.RRL=[-Lh ; -W  ;  -Hl];
para_Fellow_8_Points=ADAS.Fellow_8_Points;

clear Lv Lh W Hl Hu; 
 
%Front Long Range Radar Sensor
%______________________________
% sensor parameters
L=250;      % the radar maximum range in meter
gama=15;    % the divergance angle in the horizontal plane in degrees %15 from bosch data sheet
beta=0.2865;     % oriantation of the 2 layers +/-  in degrees
% calculation of the position of all sensor points relative to the center
% of gravity of the vehicle under test
% Apex=[Para.VD.Length_Front.v+0.5 0 0.2];
Apex=[Para.VD.Length_Front.v+0.5 0 0.2];

% centeral triangle
centeral_triangle_left=[Apex(1)+L  Apex(2)+L*tand(gama)  Apex(3)];
centeral_triangle_right=[Apex(1)+L  Apex(2)-L*tand(gama)  Apex(3)];
% upper triangle
% upper_triangle_left=[Apex(1)+L*cosd(beta) Apex(2)+L*tand(gama) Apex(3)+L*sind(beta)];
% upper_triangle_right=[Apex(1)+L*cosd(beta) Apex(2)-L*tand(gama) Apex(3)+L*sind(beta)];
upper_triangle_left=[Apex(1)+L Apex(2)+L*tand(gama) Apex(3)+L*sind(beta)];
upper_triangle_right=[Apex(1)+L Apex(2)-L*tand(gama) Apex(3)+L*sind(beta)];


% lower triangle
lower_triangle_left=[Apex(1)+L Apex(2)+L*tand(gama) Apex(3)-L*sind(beta)];
lower_triangle_right=[Apex(1)+L Apex(2)-L*tand(gama) Apex(3)-L*sind(beta)];

ADAS.Front_Long_Range_Radar.Apex=Apex;
ADAS.Front_Long_Range_Radar.Centeral_triangle_left=centeral_triangle_left;
ADAS.Front_Long_Range_Radar.Centeral_triangle_right=centeral_triangle_right;
ADAS.Front_Long_Range_Radar.Upper_triangle_left=upper_triangle_left;
ADAS.Front_Long_Range_Radar.Upper_triangle_right=upper_triangle_right;
ADAS.Front_Long_Range_Radar.Lower_triangle_left=lower_triangle_left;
ADAS.Front_Long_Range_Radar.Lower_triangle_right=lower_triangle_right;
ADAS.Front_Long_Range_Radar.filter_radius=250;
% para_filter_radius_long_range=ADAS.Front_Long_Range_Radar.filter_radius;

clear L gama beta Apex centeral_triangle_left centeral_triangle_right upper_triangle_left upper_triangle_right lower_triangle_left lower_triangle_right
 %%
%Front Mid Range Radar Sensor
%______________________________
% sensor parameters
L=100;      % the radar maximum range in meter
gama=60/2;    % the divergance angle in the horizontal plane in degrees %15 from bosch data sheet
beta=0.2865;     % oriantation of the 2 layers +/-  in degrees
% calculation of the position of all sensor points relative to the center
% of gravity of the vehicle under test
Apex=[Para.VD.Length_Front.v+0.5 0 0.2];
% centeral triangle
centeral_triangle_left=[Apex(1)+L  Apex(2)+L*tand(gama)  Apex(3)];
centeral_triangle_right=[Apex(1)+L  Apex(2)-L*tand(gama)  Apex(3)];
% upper triangle
% upper_triangle_left=[Apex(1)+L*cosd(beta) Apex(2)+L*tand(gama) Apex(3)+L*sind(beta)];
% upper_triangle_right=[Apex(1)+L*cosd(beta) Apex(2)-L*tand(gama) Apex(3)+L*sind(beta)];
upper_triangle_left=[Apex(1)+L Apex(2)+L*tand(gama) Apex(3)+L*sind(beta)];
upper_triangle_right=[Apex(1)+L Apex(2)-L*tand(gama) Apex(3)+L*sind(beta)];


% lower triangle
lower_triangle_left=[Apex(1)+L Apex(2)+L*tand(gama) Apex(3)-L*sind(beta)];
lower_triangle_right=[Apex(1)+L Apex(2)-L*tand(gama) Apex(3)-L*sind(beta)];

ADAS.Front_Mid_Range_Radar.Apex=Apex;
ADAS.Front_Mid_Range_Radar.Centeral_triangle_left=centeral_triangle_left;
ADAS.Front_Mid_Range_Radar.Centeral_triangle_right=centeral_triangle_right;
ADAS.Front_Mid_Range_Radar.Upper_triangle_left=upper_triangle_left;
ADAS.Front_Mid_Range_Radar.Upper_triangle_right=upper_triangle_right;
ADAS.Front_Mid_Range_Radar.Lower_triangle_left=lower_triangle_left;
ADAS.Front_Mid_Range_Radar.Lower_triangle_right=lower_triangle_right;
ADAS.Front_Mid_Range_Radar.filter_radius=150;
% para_filter_radius_Mid_range=ADAS.Front_Mid_Range_Radar.filter_radius;
clear L gama beta Apex centeral_triangle_left centeral_triangle_right upper_triangle_left upper_triangle_right lower_triangle_left lower_triangle_right

%%
%Emergency Brake Assist

ADAS.EBA.Braking_Distance_LookUpTable.velocity=[0      1      3     5      8      10   20  40   60   80   100 120  130  140 150  160 170  180   200];
ADAS.EBA.Braking_Distance_LookUpTable.Distance=[0.029  0.029  0.25  0.65   1.75   2.5  5.5 10.5 12.5 13.5 14  14.5 10.5 6   3.45 1.8 0.83 0.292 0.292];
