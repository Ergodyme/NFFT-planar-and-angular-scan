# -*- coding: utf-8 -*-
"""

Author: Galaad BARRAUD
Date: 05/05/25

"""

import pyvisa
import os
import time
import numpy as np
from datetime import datetime
import re
import glob
import csv

def find_ind(arr, freq):
    ind = []
    for index, value in enumerate(arr):
        if value == freq:
            ind.append(index)
    return ind

def file_to_col(chemin, ligne_de_depart, colonne):
    col = []
    try:
        with open(chemin,'r') as file:
            read = csv.reader(file, delimiter='\t')
            for i, row in enumerate(read):
                if i >= ligne_de_depart:
                    if colonne < len(row):
                        col.append(float(row[colonne]))
                    else:
                        col.append(None)
    except FileNotFoundError:
        print("Erreur: le fichier n'a pas été trouvé")
    except Exception as e:
        print(f"Erreur: {e}")
    return col

def extraire_valeur(chemin_fichier, li, co):
  try:
    with open(chemin_fichier, 'r') as f:
      lignes = f.readlines()
      if 0 <= li < len(lignes):
        ligne = lignes[li].strip().split()
        if 0 <= co < len(ligne):
          return ligne[co]
  except FileNotFoundError:
    print(f"Erreur : Fichier non trouvé : {chemin_fichier}")
  return None

def matrix_tps_reel(dossier, ligne_cible, colonne_cible, X, pas):
    fichiers = sorted([f for f in os.listdir(dossier) if re.match(r"Balayage_\d+\.txt", f)],key=lambda x: int(re.findall(r'\d+', x)[0]))
    nb = int(np.ceil((X/pas+1)**2))
    if int(len(fichiers) ** 0.5) == nb:
        N = int(len(fichiers) ** 0.5)
    else:
        N = nb
    matrice = np.zeros((N, N), dtype=float)
    for idx, fichier in enumerate(fichiers):
        with open(os.path.join(dossier, fichier), 'r') as f:
          lignes = f.readlines()
          if 0 <= ligne_cible < len(lignes):
            ligne = lignes[ligne_cible].strip().split()
            if 0 <= colonne_cible < len(ligne):
                valeur = ligne[colonne_cible]
        row = N - 1 - (idx // N)
        col_index = idx % N
        if (N - 1 - row) % 2 == 0:
            col = N - 1 - col_index  
        else:
            col = col_index         
        matrice[row][col] = valeur
    return matrice

def matrix(dossier, ligne_cible, colonne_cible, rot=False):
    if rot ==True:
        fichiers = sorted([f for f in os.listdir(dossier) if re.match(r"Rotation_\d+\.txt", f)],key=lambda x: int(re.findall(r'\d+', x)[0]))
    else :
        fichiers = sorted([f for f in os.listdir(dossier) if re.match(r"Balayage_\d+\.txt", f)],key=lambda x: int(re.findall(r'\d+', x)[0]))
    N = int(len(fichiers) ** 0.5)
    matrice = np.zeros((N, N), dtype=float)
    for idx, fichier in enumerate(fichiers):
        with open(os.path.join(dossier, fichier), 'r') as f:
          lignes = f.readlines()
          if 0 <= ligne_cible < len(lignes):
            ligne = lignes[ligne_cible].strip().split()
            if 0 <= colonne_cible < len(ligne):
                valeur = ligne[colonne_cible]
        row = N - 1 - (idx // N)
        col_index = idx % N
        if (N - 1 - row) % 2 == 0:
            col = N - 1 - col_index  
        else:
            col = col_index         
        matrice[row][col] = valeur
    return matrice

def matrix_single_freq(chemin_fichier, A=[-5,-5], B=[5,5], pas=1, col=3):
    try:
        N = int((B[0] - A[0])/pas + 1)
        with open(chemin_fichier, 'r') as fichier:
            lecteur_csv = csv.reader(fichier, delimiter='\t') 
            next(lecteur_csv) 
            colonnes = list(zip(*lecteur_csv))  
        meas = [float(i) for i in colonnes[col]]
        matrice = np.zeros((N, N), dtype=float)
        idx = 0
        for row in range(N-1, -1, -1):  
            if (N - 1 - row) % 2 == 0:
                for col in range(N-1, -1, -1):
                    matrice[row][col] = meas[idx]
                    idx += 1
            else:
                for col in range(N):
                    matrice[row][col] = meas[idx]
                    idx += 1
        return matrice
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{chemin_fichier}' n'a pas été trouvé.")
        return None

def file_to_array(dossier, ligne_cible, colonne_cible, rot=False):
    if rot == True:
        fichiers = sorted([f for f in os.listdir(dossier) if re.match(r"Rotation_\d+\.txt", f)],key=lambda x: int(re.findall(r'\d+', x)[0]))
    else:
        fichiers = sorted([f for f in os.listdir(dossier) if re.match(r"Balayage_\d+\.txt", f)],key=lambda x: int(re.findall(r'\d+', x)[0]))
    array = []
    for fichier in fichiers:
        with open(os.path.join(dossier, fichier), 'r') as f:
            lignes = f.readlines()
            if ligne_cible < len(lignes):
                ligne = lignes[ligne_cible].strip().split('\t')
                if colonne_cible < len(ligne):
                    array.append(float(ligne[colonne_cible]))
                else:
                    array.append(0.0)  
            else:
                array.append(0.0)
    return array

def move(entree = [2, 2, 1, 0, 1, "GPIB0::1::INSTR"]):
    axis = str(entree[0])
    units = str(entree[1])
    movement = str(entree[2])
    absolute = {"1":True, "0":False}[str(entree[3])]
    speed = int(entree[4])
    ip_adress_esp = str(entree[5])
    rm = pyvisa.ResourceManager()
    time.sleep(3)
    esp = rm.open_resource(f'{ip_adress_esp}')
    esp.timeout = 30000
    print("Connecté à :", esp.query("*IDN?")) # ask identification
    time.sleep(1)
    esp.write(f'{axis}MO')
    esp.write(f'{axis}SN{units}')
    esp.write(f'{axis}AC5')
    esp.write(f'{axis}AG5')
    speed_mode = {1:"JW5", 2:"JH10", 3:"VU15"}[speed]
    esp.write(f'{axis}{speed_mode}')
    movement_mode = f'{"PA" if absolute else "PR"}'
    esp.write(f'{axis}{movement_mode}{movement}')
    esp.write(f'{axis}WS')
    print("Deplacment terminé")
    esp.close()
    print("Connexions fermées")
    return "Deplacement terminé"

def plot(entree = ["C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad", "0", "C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad"]):
    save_path = str(entree[0])
    rot = int(entree[1])
    chemin_param = os.path.abspath(str(entree[2]))
    if rot == 0:
        theta = file_to_col(save_path, 1, 0)
        mag_S12 = file_to_col(save_path, 1, 1)
        ph_S12 = file_to_col(save_path, 1, 2)
        mag_S21 = file_to_col(save_path, 1, 3)
        ph_S21 = file_to_col(save_path, 1, 4)
        return np.concatenate((theta,mag_S12,ph_S12,mag_S21,ph_S21))
    elif rot ==1:
        A1 = int(extraire_valeur(chemin_param, 1, 6))
        A2 = int(extraire_valeur(chemin_param, 1, 7))
        pas_x = int(extraire_valeur(chemin_param, 1, 4))
        B1 = int(extraire_valeur(chemin_param, 1, 8))
        B2 = int(extraire_valeur(chemin_param, 1, 9))
        pas_y = int(extraire_valeur(chemin_param, 1, 5))
        mag_S12 = matrix_single_freq(os.path.abspath(save_path), [A1,B1], [A2,B2], pas_x, pas_y, col=2).flatten()
        ph_S12 = matrix_single_freq(os.path.abspath(save_path), [A1,B1], [A2,B2], pas_x, pas_y, col=3).flatten()
        mag_S21 = matrix_single_freq(os.path.abspath(save_path), [A1,B1], [A2,B2], pas_x, pas_y, col=4).flatten()
        ph_S21 = matrix_single_freq(os.path.abspath(save_path), [A1,B1], [A2,B2], pas_x, pas_y, col=5).flatten()
        return np.concatenate((mag_S12,mag_S21,ph_S12,ph_S21))  

def move_meas(axis, units, movement, absolute, speed, esp, sign):
    time.sleep(3)
    esp.timeout = 30000
    print("Connecté à :", esp.query("*IDN?")) # ask identification
    time.sleep(1)
    esp.write(f'{axis}MO')
    esp.write(f'{axis}SN{units}')
    esp.write(f'{axis}AC5')
    esp.write(f'{axis}AG5')
    speed_mode = {1:"JW5", 2:"JH10", 3:"VU15"}[speed]
    esp.write(f'{axis}{speed_mode}')
    movement_mode = f'{"PA" if absolute else "PR"}'
    esp.write(f'{axis}{movement_mode}{sign}{movement}')
    esp.write(f'{axis}WS')

def meas_and_save(channel, state_avg, count_avg, axis, trace_name, hh, start_freq, stop_freq, points, vna, esp, save_path):
    if state_avg: # if state_avg=True: turn off and on the averaging before tacking the measure to make sure the averaging is done at a given position 
        vna.write(f'SENSe{channel}:AVERage OFF')
        time.sleep(0.1)
        vna.write(f'SENSe{channel}:AVERage ON')
        time.sleep(1)
        vna.write(f'SENSe{channel}:AVERage:COUNt {count_avg}') # set the average count to count_avg
        for z in range(count_avg): # take count_avg measures to correctly average the signals
            vna.write(f'INITiate{channel}:IMMediate')
            vna.write('*WAI')
    else: 
        esp.write(f'{axis[0]}WS')
        esp.write(f'{axis[1]}WS')
        vna.write(f'SENSe{channel}:AVERage OFF')
        vna.write(f'INITiate{channel}:IMMediate')
        vna.write('*WAI')
################################################################################################
# Saving in a file
################################################################################################
    all_magnitudes = []
    all_phases = []
    freq_data = np.linspace(int(start_freq), int(stop_freq), int(points))
    for trace in trace_name:
        vna.write(f'CALCulate{channel}:PARameter:SELect "{trace}"')
        time.sleep(1)
        vna.write(f'CALCulate{channel}:FORMat MLOG') # magnitude (dB)
        time.sleep(1)
        mag_data = vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA') # 'FDATA' -> real part of the data
        vna.write(f'CALCulate{channel}:FORMat PHAS') # phase (°)
        time.sleep(1)
        phase_data = vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA')
        all_magnitudes.append(mag_data)
        all_phases.append(phase_data)
    date = datetime.now().strftime("%m-%d-%Y")
    esp.write(f'{axis[0]}TP?') # ask the esp the x value
    x = esp.read()
    time.sleep(0.5)
    esp.write(f'{axis[1]}TP?') # ask the esp the y value
    y = esp.read()
    file_name = f"Balayage_{hh}.txt"
    os.makedirs(save_path, exist_ok=True)
    full_path = os.path.join(save_path, file_name)
    with open(full_path, 'w') as f:
        header = ["Frequency (Hz)"]
        for trace in trace_name:
            header.append(f"Magnitude_{trace}")
            header.append(f"Phase_{trace}")
        if state_avg:
            header.append(f'{date}_{trace_name}_strat={start_freq/1E9}GHz_strop={stop_freq/1E9}GHz_average={count_avg}_[x_y]=[{x}_{y}]')
        else:
            header.append(f'{date}_{trace_name}_strat={start_freq/1E9}GHz_strop={stop_freq/1E9}GHz_avrage=False_[x_y]=[{x}_{y}]')
        f.write("\t".join(header) + "\n")
        for l in range(points):
            line = [f"{freq_data[l]:.2f}"]
            for mag, phase in zip(all_magnitudes, all_phases):
                line.append(f"{mag[l]:.4f}")
                line.append(f"{phase[l]:.4f}")
            f.write("\t".join(line) + "\n")
    return x, y    

def Balayage_2D_VNA_ESP(entree = [1, 2, 10, 0, 1, 5, 110E9, 170E9, 201, 1000, "WR6.5_Galaad.csa", "GPIB1::16::INSTR", "GPIB1::1::INSTR", "C:\\Users\\Thomas\\Documents\\chahadih\\vna_data_test_galaad", 140E9, "Comp"]):
    ################################################################################################
    # parameters
    ################################################################################################
    channel = 1
    speed = 3
    accel = "10"
    deccel = "10"
    trace_name = ["S12","S21"]
    ################################################################################################
    # entries
    ################################################################################################
    axis = {4:["1","2"], 5:["2","3"], 6:["1","3"]}[int(entree[0])]
    units = str(entree[1]) # 0 = encoder count, 1 = motor step, 2 = millimeter, 3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient, 9 = radian, 10 = milliradian, 11 = microradian
    B = int(entree[2])
    A = int(entree[3])
    pas = int(entree[4])
    count_avg = int(entree[5])
    if count_avg == 0:
        state_avg = False
    else:
        state_avg = True
    start_freq = int(entree[6]) * 10**9
    stop_freq = int(entree[7]) * 10**9
    points = int(entree[8])
    IFBW = int(entree[9])
    band = str(entree[10])
    ip_adress_vna = str(entree[11])
    ip_adress_esp = str(entree[12])
    save_path = str(entree[13])
    freq_plot = int(entree[14]) * 10**9
    File_name = str(entree[15])
    ################################################################################################
    # init
    ################################################################################################
    rm = pyvisa.ResourceManager()
    vna = rm.open_resource(f'{ip_adress_vna}')
    vna.timeout = 30000  # timeout of 30 sec
    esp = rm.open_resource(f'{ip_adress_esp}')
    esp.timeout = 30000
    esp.write_termination = '\r'
    esp.read_termination = '\r'
    time.sleep(1)
    vna.write(':MMEMory:LOAD:FILE "%s"' % (f'D:/{band}')) # call the saved state and calset data
    time.sleep(2)
    vna.write(f'CALCulate{channel}:PARameter:DELete:ALL') # delete all previous parameters
    vna.write(f'SENSe{channel}:FREQuency:STARt {start_freq}') # set the starting frequence to start_freq
    vna.write(f'SENSe{channel}:FREQuency:STOP {stop_freq}') # set the finishing frequence to stop_freq
    vna.write(f'SENSe{channel}:SWEep:POINts {points}') # set the number of point to points
    vna.write(f'SENSe{channel}:BAND {IFBW}') # set the IFBW
    vna.write(f'INITiate{channel}:CONTinuous OFF') # turn off the continuous measure mode
    time.sleep(2)
    print(f"Canal {channel} configuré : start={start_freq}, stop={stop_freq}, points={points}")
    time.sleep(1)
    for j, trace in enumerate(trace_name):
        vna.write(f'CALCulate{channel}:PARameter:DEFine'+' '+f"{trace}"+","+f'{trace}') # definie a new trace
        vna.write(f'CALCulate{channel}:PARameter:SELect "{trace}"') # select the new trace
        vna.write(f'DISPlay:WINDow{j+1}:STATe ON') # turn on the window display
        vna.write(f'DISPlay:WINDow{j+1}:TRACe{j+1}:FEED "{trace}"') # put the new trace into the window
        time.sleep(1)
        vna.write(f':DISPlay:WINDow{j+1}:TRACe{j+1}:Y:AUTO') # autoscale the trace
        print(f"Trace {trace} ajoutée à la fenêtre {j+1}")
    for axe in axis:
        esp.write(f'{axe}MO') # turn on the axis
        esp.write(f'{axe}SN{units}') # set the unit of the axis: 0 = encoder count, 1 = motor step, 2 = millimeter, 3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient, 9 = radian, 10 = milliradian, 11 = microradian
        esp.write(f'{axe}AC{accel}') # set the axis acceleration
        esp.write(f'{axe}AG{deccel}') # set the axis decceleration
        if speed==1:
            speed_mode = "JW5" # slow
        elif speed==2:
            speed_mode = "JH10" # medium
        elif speed==3:
            speed_mode = "VU15" # fast
        esp.write(f'{axe}{speed_mode}') # set the speed mode
    if start_freq == stop_freq:
        vna.write(f'SENSe{channel}:SWEep:POINts 1') # set the number of point to 1
        print("Balayage mono-fréquence:")
    freq_data = np.linspace(int(start_freq), int(stop_freq), int(points))
    ################################################################################################
    # sweep spacial parameters
    ################################################################################################
    esp.write(f'{axis[0]}PA{A}')
    esp.write(f'{axis[0]}WS')
    esp.write(f'{axis[1]}PA{A}')
    esp.write(f'{axis[1]}WS')
    L_tot_1 = int(np.round((int(B)-int(A))/int(pas),0))
    L_tot_2 = int(np.round((int(B)-int(A))/int(pas) + 1,0))
    nb_tot_position = int(np.ceil((1 + (int(B)-int(A)) / int(pas) )**2))
    hh = 1 # hh tracks the number of measurements
    xx = []
    yy = []
    unit = {0:"encoder_count", 1:"motor_step", 2:"mm", 3:"µm", 4:"inches", 5:"milli-inches", 6:"micro-inches", 7:"deg", 8:"grad", 9:"rad", 10:"mili-rad", 11:"µ-rad"}[int(units)]
    ligne_cible = int(find_ind(freq_data, freq_plot)[0])
    ################################################################################################
    # preset file creation
    ################################################################################################  
    file_name = f"{File_name}_parameters.txt"
    os.makedirs(save_path, exist_ok=True)    
    full_path = os.path.join(save_path, file_name)
    with open(full_path, 'w') as f:
        header = ["start_freq (Hz)", "stop_freq (Hz)", "number_of_point", "average", f"step_x_y ({unit})", f"x_min ({unit})", f"x_max ({unit})", f"y_min ({unit})", f"y_max ({unit})"]
        f.write("\t".join(header) + "\n")
        if state_avg:
            line = [f"{start_freq}",  f"{stop_freq}", f"{points}", f"{count_avg}", f"{pas}", f"{A}", f"{B}", f"{A}", f"{B}", f"{A}", f"{B}"]
        else: 
            line = [f"{start_freq}",  f"{stop_freq}", f"{points}", "0", f"{pas}", f"{A}", f"{B}", f"{A}", f"{B}", f"{A}", f"{B}"]
        f.write("\t".join(line) + "\n")
    ################################################################################################
    # this is the 2D-sweeping script 
    ################################################################################################
    for i in range(L_tot_2):
        for j in range(L_tot_1):
            if i%2 ==0:
                signe = "+" # change sign to make the arm go back and forth
            else:
                signe = "-"
            x, y = meas_and_save(channel, state_avg, count_avg, axis, trace_name, hh, start_freq, stop_freq, points, vna, esp, save_path)  
            xx.append(x)
            yy.append(y)
            mag_S12 = matrix_tps_reel(save_path, ligne_cible, 1, int(B-A), pas)
            ph_S12 = matrix_tps_reel(save_path, ligne_cible, 2, int(B-A), pas)
            mag_S21 = matrix_tps_reel(save_path, ligne_cible, 3, int(B-A), pas)
            ph_S21 =  matrix_tps_reel(save_path, ligne_cible, 4, int(B-A), pas)
            move_meas(axis[0], units, pas, False, speed, esp, signe)
            hh = hh + 1
            yield np.concatenate((mag_S12,mag_S21,ph_S12,ph_S21))
        x, y = meas_and_save(channel, state_avg, count_avg, axis, trace_name, hh, start_freq, stop_freq, points, vna, esp, save_path)  
        xx.append(x)
        yy.append(y)
        mag_S12 = matrix_tps_reel(save_path, ligne_cible, 1, int(B-A), pas)
        ph_S12 = matrix_tps_reel(save_path, ligne_cible, 2, int(B-A), pas)
        mag_S21 = matrix_tps_reel(save_path, ligne_cible, 3, int(B-A), pas)
        ph_S21 =  matrix_tps_reel(save_path, ligne_cible, 4, int(B-A), pas)
        move_meas(axis[1], units, pas, False, speed, esp, "+")
        hh = hh + 1
        yield np.concatenate((mag_S12,mag_S21,ph_S12,ph_S21))
    ################################################################################################
    # one file to rule them all (create a final data file at the end of the acquisition to compile the data at a given frequency)
    ################################################################################################  
    freq_data = np.linspace(start_freq, stop_freq, points)
    date = datetime.now().strftime("%m-%d-%Y")
    for freq_idx in range(points):
        target_frequency = freq_data[freq_idx]
        ligne_freq = freq_idx + 1
        file_name = f"{File_name}_{target_frequency/1E9:.3f}GHz.txt"
        full_path = os.path.join(save_path, file_name)
        all_mag = []
        all_phase = []
        for i, trace in enumerate(trace_name):
            mag_col = 1 + 2 * i      
            phase_col = mag_col + 1
            magnitudes = file_to_array(save_path, ligne_freq, mag_col)
            phases = file_to_array(save_path, ligne_freq, phase_col)
            all_mag.append(magnitudes)
            all_phase.append(phases)
        with open(full_path, 'w') as f:
            header = ["x", "y"]
            for trace in trace_name:
                header.extend([f"Magnitude_{trace}", f"Phase_{trace}"])
            if state_avg:
                header.append(f'{date}_freq={freq_data[freq_idx]/1E9}GHz_lbd={299792458/freq_data[freq_idx]}m_xmin={A}_xmax={B}_y_min={A}_ymax={B}_stepxy={pas}_average={count_avg}')
            else:
                header.append(f'{date}_freq={freq_data[freq_idx]/1E9}GHz_lbd={299792458/freq_data[freq_idx]}m_xmin={A}_xmax={B}_y_min={A}_ymax={B}_stepxy={pas}')
            f.write("\t".join(header) + "\n")
            for pos_idx in range(nb_tot_position):
                line = [f"{xx[pos_idx]}", f"{yy[pos_idx]}"]
                for trace_idx in range(len(trace_name)):
                    if pos_idx < len(all_mag[trace_idx]):
                        mag = all_mag[trace_idx][pos_idx]
                        phase = all_phase[trace_idx][pos_idx]
                        line.extend([f"{mag:.4f}", f"{phase:.4f}"])
                    else:
                        line.extend(["0.0000", "0.0000"])
                f.write("\t".join(line) + "\n")
        print(f"Fichier créé: {file_name}")
    print("Traitement terminé!")
    ################################################################################################
    # delete all "Balayage_i.txt" files
    ################################################################################################  
    motif = os.path.join(save_path, "Balayage_*.txt")
    fichiers = glob.glob(motif)
    for fichier in fichiers:
        os.remove(fichier)
        print(f"Supprimé : {fichier}")
    ################################################################################################
    # returning home, ask for error and closing connections
    ################################################################################################
    for axe in axis: 
        esp.write(f'{axe}PA0') # return to zero when the sweep is finished
        esp.write(f'{axe}WS')
    vna.close() 
    esp.close()
    print("Mesures terminées")
    print("Connexions fermées")
    mag_S12 = matrix_single_freq(os.path.join(save_path,f"{File_name}_{freq_plot/1E9:.3f}GHz.txt"), [A,A], [B,B], pas, col=2)
    ph_S12 = matrix_single_freq(os.path.join(save_path,f"{File_name}_{freq_plot/1E9:.3f}GHz.txt"), [A,A], [B,B], pas, col=3)
    mag_S21 = matrix_single_freq(os.path.join(save_path,f"{File_name}_{freq_plot/1E9:.3f}GHz.txt"), [A,A], [B,B], pas, col=4)
    ph_S21 = matrix_single_freq(os.path.join(save_path,f"{File_name}_{freq_plot/1E9:.3f}GHz.txt"), [A,A], [B,B], pas, col=5)
    yield np.concatenate((mag_S12,mag_S21,ph_S12,ph_S21))

def Rotation_VNA_ESP(entree = [1, 2, 10, 0, 1, 5, 110E9, 170E9, 201, 1000, "WR6.5_Galaad.csa", "-to+", 140, "GPIB1::16::INSTR", "GPIB1::2::INSTR", "C:\\Users\\Thomas\\Documents\\chahadih\\vna_data_test_galaad", "rot"]):
    ################################################################################################
    # parameters
    ################################################################################################
    channel = 1
    accel = "10"
    deccel = "10"
    speed = 3
    trace_name = ["S12","S21"]
    ################################################################################################
    # entries
    ################################################################################################
    axis = {"1":1, "2":2, "3":3}[entree[0]]
    units = str(entree[1]) # 0 = encoder count, 1 = motor step, 2 = millimeter, 3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient, 9 = radian, 10 = milliradian, 11 = microradian
    theta_max = str(entree[2])
    theta_min = str(entree[3])
    pas = str(entree[4])
    count_avg = str(entree[5])
    if count_avg == "0":
        state_avg = False
    else:
        state_avg = True
    start_freq = str(entree[6])
    stop_freq = str(entree[7])
    points = str(entree[8])
    IFBW = str(entree[9])
    band = str(entree[10])
    sens = str(entree[11])
    freq_plot = int(entree[12]) * 10**9
    ip_adress_vna = str(entree[13])
    ip_adress_esp = str(entree[14])
    save_path = str(entree[15])
    File_name = str(entree[16])
    ################################################################################################
    # conexion to the vna and esp
    ################################################################################################
    rm = pyvisa.ResourceManager()
    vna = rm.open_resource(f'{ip_adress_vna}')
    vna.timeout = 30000  # timeout of 30 sec
    esp = rm.open_resource(f'{ip_adress_esp}')
    esp.timeout = 30000
    print("Connecté à :", esp.query("*IDN?")) # ask identification
    print("Connecté à :", vna.query("*IDN?")) # ask identification
    time.sleep(1)
    vna.write(':MMEMory:LOAD:FILE "%s"' % (f'D:/{band}')) # call the saved state and calset data
    time.sleep(2)
    vna.write(f'CALCulate{channel}:PARameter:DELete:ALL') # delete all previous parameters
    vna.write(f'SENSe{channel}:FREQuency:STARt {start_freq}') # set the starting frequence to start_freq
    vna.write(f'SENSe{channel}:FREQuency:STOP {stop_freq}') # set the finishing frequence to stop_freq
    vna.write(f'SENSe{channel}:SWEep:POINts {points}') # set the number of point to points
    vna.write(f'SENSe{channel}:BAND {IFBW}') # set the IFBW
    vna.write(f'INITiate{channel}:CONTinuous OFF') # turn off the continuous measure mode
    time.sleep(2)
    print(f"Canal {channel} configuré : start={start_freq}, stop={stop_freq}, points={points}")
    time.sleep(1)
    for i in range(len(trace_name)):
        vna.write(f'CALCulate{channel}:PARameter:DEFine'+' '+f"{trace_name}"+","+f'{trace_name}') # definie a new trace
        vna.write(f'CALCulate{channel}:PARameter:SELect "{trace_name}"') # select the new trace
        vna.write(f'DISPlay:WINDow{i+1}:STATe ON') # turn on the window display
        vna.write(f'DISPlay:WINDow{i+1}:TRACe{i+1}:FEED "{trace_name}"') # put the new trace into the window
        time.sleep(1)
        vna.write(f':DISPlay:WINDow{i+1}:TRACe{i+1}:Y:AUTO') # autoscale the trace
        print(f"Trace {trace_name} ajoutée à la fenêtre {i+1}")
    ################################################################################################
    # I don't know why the motion controller needs this (but it does)
    ################################################################################################
    esp.write_termination = '\r'
    esp.read_termination = '\r'
    ################################################################################################
    # give parameters to the axis (acceleration, speed mode...)
    ################################################################################################
    esp.write(f'{axis}MO')
    esp.write(f'{axis}SN{units}')
    esp.write(f'{axis}AC{accel}')
    esp.write(f'{axis}AG{deccel}')
    speed_mode = {1: "JW5", 2: "JH10", 3: "VU15"}[speed]
    esp.write(f'{axis}{speed_mode}')
    time.sleep(2)
    ################################################################################################
    # sweep spacial parameters
    ################################################################################################
    nb_tot_position = int(np.ceil(np.abs(1 + (theta_max - theta_min) / pas )))
    sortie = []
    if sens == '-to+':
        sign = '+'
        theta_min_sign = theta_min
    elif sens == '+to-':
        sign = '-'
        theta_min_sign = -theta_min
    esp.write(f'{axis}PA{theta_min_sign}')
    esp.write(f'{axis}WS')
    time.sleep(3)
    start_freq = float(vna.query(f'SENSe{channel}:FREQuency:STARt?')) # ask the vna the value of start_freq
    stop_freq = float(vna.query(f'SENSe{channel}:FREQuency:STOP?')) # ask the vna the value of stop_freq
    points = int(vna.query(f'SENSe{channel}:SWEep:POINts?')) # ask the vna the number of point
    if start_freq == stop_freq:
        vna.write(f'SENSe{channel}:SWEep:POINts 1') # set the number of point to 1
        print("Balayage mono-fréquence:")
    unit = {0:"encoder_count", 1:"motor_step", 2:"mm", 3:"µm", 4:"inches", 5:"milli-inches", 6:"micro-inches", 7:"deg", 8:"grad", 9:"rad", 10:"mili-rad", 11:"µ-rad"}[int(units)]
    
    ################################################################################################
    # preset file creation
    ################################################################################################  
    file_name = f"{File_name}_parameters.txt"
    os.makedirs(save_path, exist_ok=True)    
    full_path = os.path.join(save_path, file_name)
    with open(full_path, 'w') as f:
        header = ["start_freq (Hz)", "stop_freq (Hz)", "number_of_point", "average", f"step ({unit})", f"theta_min ({unit})", f"theta_max ({unit})", "unit"]
        f.write("\t".join(header) + "\n")
        if state_avg:
            line = [f"{start_freq}",  f"{stop_freq}", f"{points}", f"{count_avg}", f"{pas}", f"{theta_min}", f"{theta_max}", f"{unit}"]
        else: 
            line = [f"{start_freq}",  f"{stop_freq}", f"{points}", "0", f"{pas}", f"{theta_min}", f"{theta_max}", f"{unit}"]
        f.write("\t".join(line) + "\n")
    ################################################################################################
    # this is the angular scan script
    ################################################################################################
    hh = 1 # hh tracks the number of measurements
    theta_val = []
    freq_data = np.linspace(int(start_freq), int(stop_freq), int(points))
    ligne_cible = int(find_ind(freq_data, freq_plot)[0])
    for i in range(nb_tot_position):
        if state_avg: # if state_avg=True: turn off and on the averaging before tacking the measure to make sure the averaging is done at a given position
            vna.write(f'SENSe{channel}:AVERage OFF')
            time.sleep(0.1)
            vna.write(f'SENSe{channel}:AVERage ON')
            time.sleep(1)
            vna.write(f'SENSe{channel}:AVERage:COUNt {count_avg}') # set the average count to count_avg
            for z in range(count_avg): # take count_avg measures to correctly average the signals
                vna.write(f'INITiate{channel}:IMMediate')
                vna.write('*WAI')
        else:
            vna.write(f'SENSe{channel}:AVERage OFF')
            vna.write(f'INITiate{channel}:IMMediate')
            vna.write('*WAI')
        freq_data = np.linspace(start_freq, stop_freq, points)
        all_magnitudes = []
        all_phases = []
        for trace in trace_name:
            vna.write(f'CALCulate{channel}:PARameter:SELect "{trace}"')
            time.sleep(2)
            vna.write(f'CALCulate{channel}:FORMat MLOG') # magnitude (dB)
            time.sleep(2)
            mag_data = vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA') # 'FDATA' -> real part of the data
            vna.write(f'CALCulate{channel}:FORMat PHAS') # phase (°)
            time.sleep(2)
            phase_data = vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA')
            all_magnitudes.append(mag_data)
            all_phases.append(phase_data)
        esp.write(f'{axis}TP?') # ask the esp the theta value
        esp.write(f'{axis}PA?') # ask the esp the theta value
        esp.write(f'{axis}MO')
        theta = esp.read()
        esp.write(f'{axis}MO')
        theta_val.append(theta)
        time.sleep(0.5)
    ################################################################################################
    # save the data in a file
    ################################################################################################
        date = datetime.now().strftime("%m-%d-%Y")
        file_name = f"Rotation_{hh}.txt"
        os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, file_name)
        with open(full_path, 'w') as f:
            header = ["Frequency (Hz)"]
            for trace in trace_name:
                header.append(f"Magnitude_{trace}")
                header.append(f"Phase_{trace}")
            if state_avg:
                header.append(f'{date}_{trace_name}_freq={start_freq/1E9}GHz_average={count_avg}')
            else:
                header.append(f'{date}_{trace_name}_freq={start_freq/1E9}GHz')
            f.write("\t".join(header) + "\n")
            for l in range(points):
                line = [f"{freq_data[l]:.2f}"]
                for mag, phase in zip(all_magnitudes, all_phases):
                    line.append(f"{mag[l]:.4f}")
                    line.append(f"{phase[l]:.4f}")
                f.write("\t".join(line) + "\n")
        print(f"Mesure {hh}/{int(nb_tot_position)}")
        if i < nb_tot_position - 1: # avoid macking too musch measurements
            esp.write(f'{axis}PR{sign}{pas}')
            esp.write(f'{axis}WS')
            time.sleep(2)
        hh = hh+1
        mag_S12 = matrix(save_path, ligne_cible, 1, True)
        ph_S12 = matrix(save_path, ligne_cible, 1, True)
        mag_S21 = matrix(save_path, ligne_cible, 1, True)
        ph_S21 =  matrix(save_path, ligne_cible, 1, True)
        yield np.concatenate((theta_val,mag_S12,mag_S21,ph_S12,ph_S21))
    ################################################################################################
    # one file to rule them all (create a final data file at the end of the acquisition to compile the data at a given frequency)
    ################################################################################################      
    for freq_idx in range(points):
        target_frequency = freq_data[freq_idx]
        ligne_freq = freq_idx + 1
        file_name = f"{File_name}_{target_frequency/1E9:.3f}GHz.txt"
        full_path = os.path.join(save_path, file_name)
        all_mag = []
        all_phase = []
        for i, trace in enumerate(trace_name):
            mag_col = 1 + 1 * i      
            phase_col = mag_col + 1
            magnitudes = file_to_array(save_path, ligne_freq, mag_col, rot=True)
            phases = file_to_array(save_path, ligne_freq, phase_col, rot=True)
            all_mag.append(magnitudes)
            all_phase.append(phases)
        with open(full_path, 'w') as f:
            header = ["theta"]
            for trace in trace_name:
                header.extend([f"Magnitude_{trace}", f"Phase_{trace}"])
            if state_avg:
                header.append(f'{date}_freq={freq_data[freq_idx]/1E9}GHz_lbd={299792458/freq_data[freq_idx]}m_thetamin={theta_min}_thetamax={theta_max}_step={pas}_average={count_avg}')
            else:
                header.append(f'{date}_freq={freq_data[freq_idx]/1E9}GHz_lbd={299792458/freq_data[freq_idx]}m_thetamin={theta_min}_thetamax={theta_max}_step={pas}')
            f.write("\t".join(header) + "\n")
            for pos_idx in range(nb_tot_position):
                line = [f"{theta_val[pos_idx]}"]
                for trace_idx in range(len(trace_name)):
                    if pos_idx < len(all_mag[trace_idx]):
                        mag = all_mag[trace_idx][pos_idx]
                        phase = all_phase[trace_idx][pos_idx]
                        line.extend([f"{mag:.4f}", f"{phase:.4f}"])
                    else:
                        line.extend(["0.0000", "0.0000"])
                f.write("\t".join(line) + "\n")
    print("Traitement terminé!")
    ################################################################################################
    esp.write(f'{axis}PA0')
    esp.write(f'{axis}WS')
    vna.close()
    esp.close()
    print("Mesures terminées\nConnexions fermées")
    fichiers = sorted([f for f in os.listdir(save_path) if re.match(r"Rotation_\d+\.txt", f)],key=lambda x: int(re.findall(r'\d+', x)[0]))
    theta_plot = []
    mag_s12_plot = []
    phase_s12_plot = []
    mag_s21_plot = []
    phase_s21_plot = []                
    col_mag_s12 = 2
    col_phase_s12 = 3
    col_mag_s21 = 4
    col_phase_s21 = 5
    with open(save_path, 'r') as f:
        line = f.readlines()
        for idx, fichier in enumerate(fichiers):
            if line[1,idx] == freq_plot:
                theta_plot.append(extraire_valeur(save_path, line[0,idx], 1))
                mag_s12_plot.append(extraire_valeur(save_path, line[0,idx], col_mag_s12))
                phase_s12_plot.append(extraire_valeur(save_path, line[0,idx], col_phase_s12))
                mag_s21_plot.append(extraire_valeur(save_path, line[0,idx], col_mag_s21))
                phase_s21_plot.append(extraire_valeur(save_path, line[0,idx], col_phase_s21))                        
    sortie = np.concatenate((theta_plot, mag_s12_plot, phase_s12_plot, mag_s21_plot, phase_s21_plot))
    ################################################################################################
    # delete all "Rotation_i.txt" files
    ################################################################################################  
    motif = os.path.join(save_path, "Rotation_*.txt")
    fichiers = glob.glob(motif)
    for fichier in fichiers:
        os.remove(fichier)
    return sortie

def init_bal(entree = [1, 2, 10, 0, 1, 5, 110E9, 170E9, 201, 1000, "WR6.5_Galaad.csa", "GPIB1::16::INSTR", "GPIB1::1::INSTR", "C:\\Users\\Thomas\\Documents\\chahadih\\vna_data_test_galaad", 140E9, "Comp"]):
    try:
        global gene
        gene = Balayage_2D_VNA_ESP(entree)
        return True
    except Exception as e:
        print(e)
        return False
    
def meas_bal():
    return next(gene)

def init_rot(entree = [1, 2, 10, 0, 1, 5, 110E9, 170E9, 201, 1000, "WR6.5_Galaad.csa", "-to+", 140, "GPIB1::16::INSTR", "GPIB1::2::INSTR", "C:\\Users\\Thomas\\Documents\\chahadih\\vna_data_test_galaad", "rot"]):
    try:
        global gene
        gene = Rotation_VNA_ESP(entree)
        return True
    except Exception as e:
        print(e)
        return False
    
def meas_rot():
    return next(gene)
        
