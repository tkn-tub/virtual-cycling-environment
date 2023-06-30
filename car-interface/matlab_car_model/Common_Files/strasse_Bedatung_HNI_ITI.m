%Dimentions of the Road
r1=57.2;
r2=57.2;
r3=57.2;
r4=57.2;
L1=600;
L2=300;
L3=600;
L4=300;
%_________________________________________________________

%position of the starting point at each segment.

%x0=0;                                     y0=0;
x1=L1;                                    y1=0;
x2=L1+r1;                                 y2=r1;
x3=L1+r1;                                 y3=r1+L2;
x4=L1+r1-r2;                              y4=r1+L2+r2;
x5=L1+r1-r2-L3;                           y5=r1+L2+r2;
x6=L1+r1-r2-L3-r3;                        y6=r1+L2;
x7=L1+r1-r2-L3-r3;                        y7=r4;

%___________________________________________________________

%S values 

S1=L1;
S2=S1+pi/2*r1;
S3=S2+L2;
S4=S3+pi/2*r2;
S5=S4+L3;
S6=S5+pi/2*r3;
S7=S6+L4;


position_start_x=[x1 x2 x3 x4 x5 x6 x7];
position_start_y=[y1 y2 y3 y4 y5 y6 y7];
data=[r1 r2 r3 r4 L1 L2 L3 L4];
s_values=[S1 S2 S3 S4 S5 S6 S7];

clear r1 r2 r3 r4 r5 r6 r7 r8 L1 L2 L3 L4 L5 L6 L7 L8 L9 ;
clear x0 y0 x1 y1 x2 y2 x3 y3 x4 y4 x5 y5 x6 y6 x7 y7 x8 y8 x9 y9 x10 y10 x11 y11 x12 y12 x13 y13 x14 y14 x15 y15 x16 y16;
clear S1 S2 S3 S4 S5 S6 S7 S8 S9 S10 S11 S12 S13 S14 S15 S16;



% segment1EndThirdLine = 600; 
% segment2EndThirdLine = 600+2*pi*57.2/4;
% segment3EndThirdLine = 600+2*pi*57.2/4+300;
% segment4EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4;
% segment5EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600;
% segment6EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4;
% segment7EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4+300;
% segment8EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4+300+2*pi*57.2/4;
% segementEnd=[segment1EndThirdLine segment2EndThirdLine segment3EndThirdLine segment4EndThirdLine segment5EndThirdLine segment6EndThirdLine segment7EndThirdLine segment8EndThirdLine];
% clear segment1EndThirdLine segment2EndThirdLine segment3EndThirdLine segment4EndThirdLine segment5EndThirdLine segment6EndThirdLine segment7EndThirdLine segment8EndThirdLine;



%% Initialisations of the road model (s,t) --> (x,y)

% Set curve radius of the third line in meter
% This value is not to be changed as it will affect the whole calculations
% The road 3D model was built according to this value
rad3rdLine = 57.2;
% Set lane width in meter
% This value is not to be changed as it will affect the whole calculations
% The road 3D model was built according to this value
laneWidth = 3.6;

% Set the end limits of road segments
% The limits are not to be changed as it will affect the whole calculations
% The road 3D model was built according to these segments limits
% Set limit of 1st segment (straight line)
segment1EndThirdLine = 600;
% Set limit of 2nd segment (curve)
segment2EndThirdLine = 600+2*pi*57.2/4;
% Set limit of 3rd segment (straight line)
segment3EndThirdLine = 600+2*pi*57.2/4+300;
% Set limit of 4th segment (curve)
segment4EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4;
% Set limit of 5th segment (straight line)
segment5EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600;
% Set limit of 6th segment (curve)
segment6EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4;
% Set limit of 7th segment (straight line)
segment7EndThirdLine = 600+2*pi*57.2/4+300+2*pi*57.2/4+600+2*pi*57.2/4+300;
% Set limit of 8th segment (curve)
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