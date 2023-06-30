close all
%engine specs
power_max=140000;
omega_Pmax=4500;
omega_max=6000;

% calculation of the engine table
p1=1;
p2=3-2*p1;
p3=2-p1;
chek1=p1+p2-p3-1;   %should equal zero     
chek2=p1+2*p2-3*p3; %should equal zero

omega=linspace(0,omega_max,101);
w=omega/omega_Pmax;
p_w=p1.*w+p2.*(w.^2)-p3.*(w.^3);
g=(power_max/(omega_Pmax*2*pi/60)).*(p_w./w);
g(1)=(power_max/(omega_Pmax*2*pi/60));

% [a,b,c,d]=	drive_enginemodel('MaskGasoline');
% plot(a,c,'b')
% hold on
% plot(omega,g,'r')

eng_speed=omega;
torque=g;


save engine_table eng_speed torque omega_max  % saving the table
 