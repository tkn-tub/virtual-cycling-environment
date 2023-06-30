%% Initialisations of the road model (s,t) --> (x,y)
%--------------------------------------------------
% Set curve radius of the third line [m]
% This value is not to be changed as it will affect the whole calculations
% The road 3D model was built according to this value
rad3rdLine = 57.2;
% Set lane width [m]
% This value is not to be changed as it will affect the whole calculations
% The road 3D model was built according to this value
laneWidth = 3.6;
% Set the end limits of road segments
% The limits are not to be changed as it will affect the whole calculations
% The road 3D model was built according to these segments limits
% Set limit of 1st segment (straight line) [m]
segment1EndThirdLine = 600;
% Set limit of 2nd segment (curve) [m]
segment2EndThirdLine = 600+2*pi*57.2/4;
% Set limit of 3rd segment (straight line) [m]
segment3EndThirdLine = 600+2*pi*57.2/4+300;
% Set limit of 4th segment (curve) [m]
segment4EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4;
% Set limit of 5th segment (straight line) [m]
segment5EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600;
% Set limit of 6th segment (curve)[m]
segment6EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4;
% Set limit of 7th segment (straight line) [m]
segment7EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4+300;
% Set limit of 8th segment (curve) [m]
segment8EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4+300+2*pi*57.2/4;

% Pack all segments limits in one vector
segmentLimits = [segment1EndThirdLine ...
                 segment2EndThirdLine ...         
                 segment3EndThirdLine ...
                 segment4EndThirdLine ...
                 segment5EndThirdLine ...
                 segment6EndThirdLine ...
                 segment7EndThirdLine ...
                 segment8EndThirdLine ...
                 ];
             
%% Initialisations of the traffic model
%--------------------------------------
% Set the vision range of the main vehicle [m]
visionRange = 150; 
% Set the s-velocities of the traffic vehicles [km/h]
setVelS = [100 90 80 70 110 90 80 70 100 120];
% Set the t-positions of the traffic vehicles [m]
% Allowed values: -1.8, -5.4, +1.8, +5.4
setPosT = [-1.8 -5.4 -1.8 -5.4 -1.8 -5.4 -1.8 -5.4 -1.8 -5.4];
% Set desired distance between any two traffic vehicles in same lame [m]
distSameLane = 60;
% Set the rate of speed increase (acceleration)
accelS = [20 20 20 20 20 20 20 20 20 20]; 
% Set the rate of speed decrease (deceleration) 
decelS = [30 30 30 30 30 30 30 30 30 30];

Para.EN.InitCond.S01=200;
Para.EN.InitCond.S02=80;
Para.EN.InitCond.S03=2116-70;
Para.EN.InitCond.S04=2116-120;
Para.EN.InitCond.S05=500;
Para.EN.InitCond.S06=100;
Para.EN.InitCond.S07=800;
Para.EN.InitCond.S08=1100;
Para.EN.InitCond.S09=1400;
Para.EN.InitCond.S10=1700;
Para.EN.InitCond.S11=0;









