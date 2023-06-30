clear all
clc
load('engine_table.mat');
V4_DT;      %The parameters of Drive Train m-file
V3_VD;      %The parameters of Vehicle Dynamic m-file
radiusWheel = 16*2.54/100;
inertiaLateral = 25*(radiusWheel)^2;
X_init=0;
Y_init=1.8;
Z_init=0;
Heading_init=0;
friction_tables;
ADAS_parameters;
strasse_Bedatung_HNI_ITI;
InitialisationsEnv;


