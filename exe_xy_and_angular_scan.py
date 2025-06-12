# -*- coding: utf-8 -*-
"""

Author: Galaad BARRAUD
Date: 05/20/25
    
"""

import xy_and_angular_scan as sc

# 2D scan

vna_ip = "GPIB0::16::INSTR"  # adresse IP du VNA
motor_controller_ip = "GPIB0::1::INSTR" # adresse IP du controle moteur

meas = sc.Balayage2D_Rotation_VNA_ESP(vna_ip, motor_controller_ip)

meas.select_state_vna(band="WR6.5_Galaad.csa")
meas.setup_channel_vna(start_freq=110E9, stop_freq=170E9, points=3, IFBW=1000) #strat_freq, stop_freq et IFBW en Hz
# meas.add_trace_vna("S12",trace_number=1, window=1)
meas.add_trace_vna("S21",trace_number=1, window=1)

# 2D scan parameters
trace_name = ["S21"] # name of the scattering parameters
axis = [2,3] # number of the ESP axis
units = 2 # unit in which the coordinates of A and B and the steps are expressed in (0 = encoder count, 1 = motor step, 2 = millimeter, 3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient, 9 = radian, 10 = milliradian, 11 = microradian)
A, B = [-10,-10], [10,10] # coordinates of A and B
pas_axe1 = pas_axe2 = 0.4 # steps
state_avg, count_avg = False, 20 # average options
save_path = "C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad\\0.4" # save path for the data files
note, File_name = "", "cornet_ff_y" # optional user note and name of the final files 

meas.balayage_2D(trace_name, axis, units, A, B, pas_axe1, pas_axe2, state_avg, count_avg, save_path, note, File_name)

#%% angular scan

import xy_and_angular_scan as sc


vna_ip = "GPIB0::16::INSTR"  # adresse IP du VNA
motor_controller_ip = "GPIB0::2::INSTR" # adresse IP du controle moteur

meas = sc.Balayage2D_Rotation_VNA_ESP(vna_ip, motor_controller_ip)

meas.select_state_vna(band="WR6.5_Galaad.csa")
meas.setup_channel_vna(start_freq=110E9, stop_freq=170E9, points=201, IFBW=1000) #strat_freq, stop_freq et IFBW en Hz
meas.add_trace_vna("S12", trace_number=1, window=1)
meas.add_trace_vna("S21", trace_number=2, window=2)

# angular scan parameters
trace_name = ["S12","S21"] # name of the scattering parameters
axis = 1 # number of the ESP axis
units = 7 # unit in which the coordinates of A and B and the steps are expressed in (0 = encoder count, 1 = motor step, 2 = millimeter, 3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient, 9 = radian, 10 = milliradian, 11 = microradian)
theta_min, theta_max = -5, 5 # coordinates of A and B
sens = "-to+" # direction of the scan; -to+ for the scan to begin at theta_min and end at theta_max, and +to- for the scan to begin at theta_max and end at theta_min
pas = 1 # steps
state_avg, count_avg = True, 20 # average options
save_path = "C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad" # save path for the data files
note, File_name = "", "Rot" # optional user note and name of the final files 

meas.rotation(trace_name, axis, units, theta_max, theta_min, sens, pas, state_avg, count_avg, save_path, note, File_name)
