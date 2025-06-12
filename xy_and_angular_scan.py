# -*- coding: utf-8 -*-
"""

Author: Galaad BARRAUD
Date: 05/20/25
    
"""

import pyvisa
import os
import time
import numpy as np
from datetime import datetime
import re
import glob
import csv

def matrix(dossier, ligne_cible, colonne_cible):
    """
    This function loads and reconstructs 2D field measurement matrices from a folder of line-
    formatted text files named Balayage_#.txt. It:
    • Reads the magnitude or phase from each file (specified line and column)
    • Automatically determines the scan grid size
    • Rebuilds the matrix according to a serpentine scanning pattern

    Parameters
    ----------
    dossier : string
        Path of the directory containing the data files.
    ligne_cible : integer
        Line of the frequency that has been chosen by the user.
    colonne_cible : integer
        Column of the chosen S-parameter.

    Returns
    -------
    matrice : array of floating
        Reconstructed matrix.

    """
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
    """
    This function reconstructs a matrix from a single tab-delimited measurement file. It:
    • Reads data for a given column index
    • Builds a 2D matrix using a boustrophedon (serpentine) scan logic
    • Supports custom grid bounds and step size

    Parameters
    ----------
    chemin_fichier : string
        Path of the directory containing the data files (must include the file).
    A : array of integer or array of floating
        Start coordinates of the scan. The default is [-5,-5].
    B : array of integer or array of floating
        End coordinates of the scan.. The default is [5,5].
    pas : integer or floating
        Step size of the scan. The default is 1.
    col : integer
        Column of the chosen S-parameter. The default is 3.

    Returns
    -------
    matrice : array of floating
        Reconstructed matrix.

    """
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
    """
    This function loads and returns concatenated data from a folder of line-formatted text files
    named Balayage_#.txt or Rotaion_#.txt.
    It opens a file, stores data in the intersection between a given line and a given column, and
    concatenates it with the other data taken from the other files.

    Parameters
    ----------
    dossier : string
        Path of the directory containing the data files.
    ligne_cible : integer
        Line of the frequency that has been chosen by the user.
    colonne_cible : integer
        Column of the chosen S-parameter.
    rot : boolean
        If True the functions search for files with the name Rotation_#.txt, and if
        False, it search for files with the name Balayage_#.txt. The default is False.

    Returns
    -------
    array : array
        Concaneted data located in the intersection of the given colomn and line in each different files.

    """
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



def boustrophedon(A,B,pas_x,pas_y):
    """
    Generates the list of coordinates (x, y) for a boustrophedon path
    covering the entire grid defined by points A and B
    and the given step.

    Parameters
    ----------
    A : array of integer or array of floating
        Start coordinates of the scan.
    B : array of integer or array of floating
        End coordinates of the scan..
    pas_x : integer or floating
        Step size of the x-axis.
    pas_y : integer or floating
        Step size of the y-axis. 
    
    Returns
    -------
    parcours_full_grid : array
        A list of tuples (x, y) representing the positions to be traversed
        in boustrophedon order, covering the entire grid.
    """
    xi, yi = A
    xf, yf = B
    min_x = min(xi, xf)
    max_x = max(xi, xf)
    min_y = min(yi, yf)
    max_y = max(yi, yf)
    num_points_x = int(round((max_x - min_x) / pas_x + 1))
    num_points_y = int(round((max_y - min_y) / pas_y + 1))
    x_coords_full = np.linspace(min_x, max_x, num_points_x)
    y_coords_full = np.linspace(min_y, max_y, num_points_y)
    parcours_full_grid = []
    start_left_to_right = True 
    for i, y in enumerate(y_coords_full):
        if (start_left_to_right and i % 2 == 0) or (not start_left_to_right and i % 2 != 0):
            for x in x_coords_full:
                pos = (x, y)
                parcours_full_grid.append(pos)
        else:
            for x in reversed(x_coords_full):
                pos = (x, y)
                parcours_full_grid.append(pos)
    return parcours_full_grid

class Balayage2D_Rotation_VNA_ESP:
    
    def __init__(self, ip_address_vna, ip_adress_esp):
        """
        Establishes communication with the VNA and ESP motion controller using VISA addresses.
        It also prints the identification strings of each device.

        Parameters
        ----------
        ip_address_vna : string
            Ip address of the VNA.
        ip_adress_esp : string
            Ip adress of the ESP.

        Returns
        -------
        None.

        """
        try: 
            rm = pyvisa.ResourceManager()
            self.vna = rm.open_resource(f'{ip_address_vna}')
            self.vna.timeout = 30000  # timeout of 30 sec
            self.esp = rm.open_resource(f'{ip_adress_esp}')
            self.esp.timeout = 30000
            print("Connecté à :", self.esp.query("*IDN?")) # ask identification
            print("Connecté à :", self.vna.query("*IDN?")) # ask identification
        except Exception as e:
            print(f"erreur lors de l'initialisation: {e}")
        
    def select_state_vna(self, band="WR6.5_Galaad.csa"):
        """
        Loads a saved VNA measurement state.
        Be sure to use only measurement state files named "WR.<x>_Galaad.csa" (for example:
        WR6.5_Galaad.csa)

        Parameters
        ----------
        band : string
            Name of the band that has to be loaded. The default is "WR6.5_Galaad.csa".

        Returns
        -------
        None.

        """
        try:
            self.vna.write(':MMEMory:LOAD:FILE "%s"' % (f'D:/{band}')) # call the saved state and calset data 
            time.sleep(2)
        except Exception as e:
            print(f"erreur lors de la selection de la bande: {e}")

    def setup_channel_vna(self, start_freq=1E9, stop_freq=3E9, points=201, IFBW=1000): 
        """
        Configures a VNA channel.

        Parameters
        ----------
        start_freq : integer or floating
            Start frequency (in Hz) of the sweep. The default is 1E9.
        stop_freq : integer or floating
            Stop frequency (in Hz) of the sweep. The default is 3E9.
        points : integer
            Number of points/frequency in the frequency sweep. The default is 201.
        IFBW : integer or floating
            Bandwidth (in Hz) of the low-pass filter at the mixer output, before detection. The default is 1000.

        Returns
        -------
        None.

        """
        try:
            channel = 1
            self.vna.write(f'CALCulate{channel}:PARameter:DELete:ALL') # delete all previous parameters
            self.vna.write(f'SENSe{channel}:FREQuency:STARt {start_freq}') # set the starting frequence to start_freq
            self.vna.write(f'SENSe{channel}:FREQuency:STOP {stop_freq}') # set the finishing frequence to stop_freq
            self.vna.write(f'SENSe{channel}:SWEep:POINts {points}') # set the number of point to points
            self.vna.write(f'SENSe{channel}:BAND {IFBW}') # set the IFBW
            self.vna.write(f'INITiate{channel}:CONTinuous OFF') # turn off the continuous measure mode
            time.sleep(2)
            print(f"Canal {channel} configuré : start={start_freq}, stop={stop_freq}, points={points}")
        except Exception as e:
            print(f"erreur lors du stetup du cannal de mesure: {e}")
    
    def add_trace_vna(self, trace_name="S21", trace_number=1, window=1):
        """
        Adds and displays a new measurement trace on the VNA.

        Parameters
        ----------
        trace_name : string
            Name of the scattering parameter. The default is "S21".
        trace_number : integer
            Number of the trace to be displayed (trace_number ∈ [1,4]). The default is 1.
        window : integer
            Number of the window you want the trace to be displayed in (window ∈
            [1,4]). The default is 1.

        Returns
        -------
        None.

        """
        try: 
            channel = 1
            self.vna.write(f'CALCulate{channel}:PARameter:DEFine'+' '+f"{trace_name}"+","+f'{trace_name}') # definie a new trace
            self.vna.write(f'CALCulate{channel}:PARameter:SELect "{trace_name}"') # select the new trace
            self.vna.write(f'DISPlay:WINDow{window}:STATe ON') # turn on the window display
            self.vna.write(f'DISPlay:WINDow{window}:TRACe{trace_number}:FEED "{trace_name}"') # put the new trace into the window
            time.sleep(1)
            self.vna.write(f':DISPlay:WINDow{window}:TRACe{trace_number}:Y:AUTO') # autoscale the trace
            print(f"Trace {trace_name} ajoutée à la fenêtre {window}")
        except Exception as e:
            print(f"erreur lors de l'ajout de la trace: {e}")

    def move(self, axis=2, units=2, movement=1, absolute=True, speed=1, accel=5, deccel=5):
        """
        Moves a given axis with defined parameters.

        Parameters
        ----------
        axis : integer
            ESP axis number. The default is 2.
        units : integer
            The unit of the movement (0 = encoder count, 1 = motor step, 2 = millimeter,
            3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient,
            9 = radian, 10 = milliradian, 11 = microradian). The default is 2.
        movement : integer or floating
            The distance the given axis must move. The default is 1.
        absolute : boolean
            If True, the movement will be absolute; if False, it will be relative. The default is True.
        speed : integer
            Speed mode of the axis (1 = slow, 2 = medium speed, 3 = fast). The default is 1.
        accel : integer or floating
            Acceleration of the movement (m.s−2). The default is 5.
        deccel : integer or floating
            Deceleration of the movement (m.s−2). The default is 5.

        Returns
        -------
        None.

        """
        try: 
            self.esp.write(f'{axis}MO')
            self.esp.write(f'{axis}SN{units}')
            self.esp.write(f'{axis}AC{accel}')
            self.esp.write(f'{axis}AG{deccel}')
            if speed==1:
                speed_mode = "JW5"
            elif speed==2:
                speed_mode = "JH10"
            elif speed==3:
                speed_mode = "VU15"
            self.esp.write(f'{axis}{speed_mode}')
            movement_mode = f'{"PA" if absolute else "PR"}'
            self.esp.write(f'{axis}{movement_mode}{movement}')
            self.esp.write(f'{axis}WS')
            print("Deplacment terminé")
        except Exception as e:
            print(f"erreur lors du deplacement: {e}")
            
    def define_home(self, axis=2):
        """
        Defines the current position as the zero reference for the given axis.

        Parameters
        ----------
        axis : integer
            ESP axis number. The default is 2.

        Returns
        -------
        None.

        """
        try:
            self.esp.write(f'{axis}DH') # define the zero of the axis as the current position
        except Exception as e:
            print(f"erreur lors de la définition du zero: {e}")
        
    def return_home(self, axis=2):
        """
        Returns the axis to its defined home position.

        Parameters
        ----------
        axis : integer
            ESP axis number. The default is 2.

        Returns
        -------
        None.

        """
        try:
            self.esp.write(f'{axis}PA0') # return to the defined zero of the axis
            self.esp.write(f'{axis}WS') # wait for the the arm to stop moving
        except Exception as e:
            print(f"erreur lors du retour au zero: {e}")
            
    def log_error(self):
        """
        Prints the current system error from the VNA (useful for debugging).

        Returns
        -------
        None.

        """
        self.vna.write("SYST:ERR?")
        err = self.vna.read()
        print(f'VNA ERROR: {err}')
    
    def balayage_2D(self, trace_name=["S12","S21","S11","S22"], axis=[2,3], units=2, A=[0,0], B=[5,5], pas_axe1=1, pas_axe2=1, state_avg=True, count_avg=5, save_path="C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad", note="", File_name="Compilation"):
        """
        Performs a full 2D scan between two spatial points A and B.
        The scan will begin at point A and end at point B. It will take measures at every step.

        Parameters
        ----------
        trace_name : array of string
            List of S-parameters . The default is ["S12","S21","S11","S22"].
        axis : array of integer
            List of the ESP axis. The default is [2,3].
        units : integer
            The unit of the movement (0 = encoder count, 1 = motor step, 2 = millimeter,
            3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient,
            9 = radian, 10 = milliradian, 11 = microradian). The default is 2.
        A : array of integer or array of floating
            Start coordinates of the scan. The default is [0,0].
        B : array of integer or array of floating
            End coordinates of the scan. The default is [5,5].
        pas_axe1 : integer or floating
            Step size of the axis 1. The default is 1.
        pas_axe2 : integer or floating
            Step size of the axis 2. The default is 1.
        state_avg : boolean
            If True the averaging will be on, if false it will be off. The default is True.
        count_avg : integer
            The number of measures to average on. The default is 5.
        save_path : string
            Output directory path. The default is "C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad".
        note : string
            Optional annotation. The default is "".
        File_name : string
            Name of the final files returned by the script. The default is "Compilation".

        Returns
        -------
        None.

        """
        try:
            ################################################################################################
            # parameters
            ################################################################################################
            channel=1
            accel="5"
            deccel="5"
            speed=3
            self.esp.write_termination = '\r'
            self.esp.read_termination = '\r'
            ################################################################################################
            # give parameters to the axis (acceleration, speed mode...)
            ################################################################################################
            for axe in axis:
                self.esp.write(f'{axe}MO') # turn on the axis
                self.esp.write(f'{axe}SN{units}') # set the unit of the axis: 0 = encoder count, 1 = motor step, 2 = millimeter, 3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient, 9 = radian, 10 = milliradian, 11 = microradian
                self.esp.write(f'{axe}AC{accel}') # set the axis acceleration
                self.esp.write(f'{axe}AG{deccel}') # set the axis decceleration
                if speed==1:
                    speed_mode = "JW5" # slow
                elif speed==2:
                    speed_mode = "JH10" # medium
                elif speed==3:
                    speed_mode = "VU15" # fast
                self.esp.write(f'{axe}{speed_mode}') # set the speed mode
            ################################################################################################
            # sweep spacial parameters
            ################################################################################################
            self.esp.write(f'{axis[0]}PA{A[0]}')
            self.esp.write(f'{axis[0]}WS')
            self.esp.write(f'{axis[1]}PA{A[1]}')
            self.esp.write(f'{axis[1]}WS')
            L_tot_1 = int(np.round((B[0]-A[0])/pas_axe1,0))
            L_tot_2 = int(np.round((B[1]-A[1])/pas_axe2 + 1,0))
            nb_tot_position = int(np.ceil(((1 + (B[0]-A[0]) / pas_axe1 ))*(1 + (B[1]-A[1]) / pas_axe2 )))
            time.sleep(2)
            start_freq = float(self.vna.query(f'SENSe{channel}:FREQuency:STARt?')) # ask the vna the value of start_freq
            stop_freq = float(self.vna.query(f'SENSe{channel}:FREQuency:STOP?')) # ask the vna the value of stop_freq
            points = int(self.vna.query(f'SENSe{channel}:SWEep:POINts?')) # ask the vna the number of point
            if start_freq == stop_freq:
                self.vna.write(f'SENSe{channel}:SWEep:POINts 1') # set the number of point to 1
                print("Balayage mono-fréquence:")
            hh = 1 # hh tracks the number of measurements
            parcours = boustrophedon(A, B, pas_axe1, pas_axe2)
            x_val = [float(p[0]) for p in parcours]
            y_val = [float(p[1]) for p in parcours]
            unit = {0:"encoder_count", 1:"motor_step", 2:"mm", 3:"µm", 4:"inches", 5:"milli-inches", 6:"micro-inches", 7:"deg", 8:"grad", 9:"rad", 10:"mili-rad", 11:"µ-rad"}[int(units)]
            ################################################################################################
            # preset file creation
            ################################################################################################  
            file_name = f"{File_name}_parameters.txt"
            os.makedirs(save_path, exist_ok=True)    
            full_path = os.path.join(save_path, file_name)
            with open(full_path, 'w') as f:
                header = ["start_freq (Hz)", "stop_freq (Hz)", "number_of_point", "average", f"step_x ({unit})", f"step_y ({unit})", f"x_min ({unit})", f"x_max ({unit})", f"y_min ({unit})", f"y_max ({unit})"]
                f.write("\t".join(header) + "\n")
                if state_avg:
                    line = [f"{start_freq}",  f"{stop_freq}", f"{points}", f"{count_avg}", f"{pas_axe1}", f"{pas_axe2}", f"{A[0]}", f"{B[0]}", f"{A[1]}", f"{B[1]}"]
                else: 
                    line = [f"{start_freq}",  f"{stop_freq}", f"{points}", "0", f"{pas_axe1}", f"{pas_axe1}", f"{A[0]}", f"{B[0]}", f"{A[1]}", f"{B[1]}"]
                f.write("\t".join(line) + "\n")
            ################################################################################################
            # this is the 2D-sweeping script 
            ################################################################################################
            for axe in axis:
                self.esp.write(f'{axe}MO')
            for i in range(L_tot_2):
                for j in range(L_tot_1):
                    ite_start_time = time.time()
                    if i%2 ==0:
                        signe = "+" # change sign to make the arm go back and forth
                    else:
                        signe = "-"
                    time.sleep(2)   
                    if state_avg: # if state_avg=True: turn off and on the averaging before tacking the measure to make sure the averaging is done at a given position 
                        self.vna.write(f'SENSe{channel}:AVERage OFF')
                        time.sleep(0.1)
                        self.vna.write(f'SENSe{channel}:AVERage ON')
                        time.sleep(1)
                        self.vna.write(f'SENSe{channel}:AVERage:COUNt {count_avg}') # set the average count to count_avg
                        for z in range(count_avg): # take count_avg measures to correctly average the signals
                            self.vna.write(f'INITiate{channel}:IMMediate')
                            self.vna.write('*WAI')
                    else: 
                        self.esp.write(f'{axis[0]}WS')
                        self.esp.write(f'{axis[1]}WS')
                        self.vna.write(f'SENSe{channel}:AVERage OFF')
                        self.vna.write(f'INITiate{channel}:IMMediate')
                        self.vna.write('*WAI')
            ################################################################################################
            # Saving in a file
            ################################################################################################
                    all_magnitudes = []
                    all_phases = []
                    freq_data = np.linspace(start_freq, stop_freq, points)
                    for trace in trace_name:
                        self.vna.write(f'CALCulate{channel}:PARameter:SELect "{trace}"')
                        time.sleep(1)
                        self.vna.write(f'CALCulate{channel}:FORMat MLOG') # magnitude (dB)
                        time.sleep(1)
                        mag_data = self.vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA') # 'FDATA' -> real part of the data
                        self.vna.write(f'CALCulate{channel}:FORMat PHAS') # phase (°)
                        time.sleep(1)
                        phase_data = self.vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA')
                        all_magnitudes.append(mag_data)
                        all_phases.append(phase_data)
                    date = datetime.now().strftime("%m-%d-%Y")
                    file_name = f"Balayage_{hh}.txt"
                    os.makedirs(save_path, exist_ok=True)
                    full_path = os.path.join(save_path, file_name)
                    with open(full_path, 'w') as f:
                        header = ["Frequency (Hz)"]
                        for trace in trace_name:
                            header.append(f"Magnitude_{trace}")
                            header.append(f"Phase_{trace}")
                        if state_avg:
                            header.append(f'{date}_{trace_name}_strat={start_freq/1E9}GHz_strop={stop_freq/1E9}GHz_average={count_avg}_[x_y]=[{x_val[hh-1]}_{y_val[hh-1]}]')
                        else:
                            header.append(f'{date}_{trace_name}_strat={start_freq/1E9}GHz_strop={stop_freq/1E9}GHz_avrage=False_[x_y]=[{x_val[hh-1]}_{y_val[hh-1]}]')
                        header.append(f'note=[{note}]')
                        f.write("\t".join(header) + "\n")
                        for l in range(points):
                            line = [f"{freq_data[l]:.2f}"]
                            for mag, phase in zip(all_magnitudes, all_phases):
                                line.append(f"{mag[l]:.4f}")
                                line.append(f"{phase[l]:.4f}")
                            f.write("\t".join(line) + "\n")
                    print(f"Mesure {hh}/{int(nb_tot_position)}")
                    self.esp.write(f'{axis[0]}PR{signe}{str(pas_axe1)}') # move the axis 1
                    self.esp.write(f'{axis[0]}WS')            
                    hh = hh+1
                    ite_end_time = time.time()
                    time_meas = ite_end_time - ite_start_time
                    if i==0 and j==0:
                        print(f"Temps estimé pour le scan: {np.round(time_meas*nb_tot_position/3600,2)}h")
                if hh>nb_tot_position: # avoid making too much measurement
                    break
                if state_avg: # if state_avg=True: turn off and on the averaging before tacking the measure to make sure the averaging is done at a given position 
                    self.vna.write(f'SENSe{channel}:AVERage OFF')
                    time.sleep(0.1)
                    self.vna.write(f'SENSe{channel}:AVERage ON')
                    self.vna.write(f'SENSe{channel}:AVERage:COUNt {count_avg}') # set the average count to count_avg
                    for z in range(count_avg): # take count_avg measures to correctly average the signals
                        self.vna.write(f'INITiate{channel}:IMMediate')
                        self.vna.write('*WAI') 
                else: 
                    self.vna.write(f'SENSe{channel}:AVERage OFF')
                    self.vna.write(f'INITiate{channel}:IMMediate')
                    self.vna.write('*WAI') 
            ################################################################################################
            # Saving in a file (for each value j we save and for each value i we also save after the j-loop)
            ################################################################################################
                all_magnitudes = []
                all_phases = []
                start_freq = float(self.vna.query(f'SENSe{channel}:FREQuency:STARt?')) # ask the vna the value of start_freq
                stop_freq = float(self.vna.query(f'SENSe{channel}:FREQuency:STOP?')) # ask the vna the value of stop_freq
                points = int(self.vna.query(f'SENSe{channel}:SWEep:POINts?')) # ask the vna the number of point
                freq_data = np.linspace(start_freq, stop_freq, points)
                for trace in trace_name:
                    self.vna.write(f'CALCulate{channel}:PARameter:SELect "{trace}"')
                    time.sleep(1)
                    self.vna.write(f'CALCulate{channel}:FORMat MLOG') # magnitude (dB)
                    time.sleep(1)
                    mag_data = self.vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA') # 'FDATA' -> real part of the data
                    self.vna.write(f'CALCulate{channel}:FORMat PHAS') # phase (°)
                    time.sleep(1)
                    phase_data = self.vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA')
                    all_magnitudes.append(mag_data)
                    all_phases.append(phase_data)
                date = datetime.now().strftime("%m-%d-%Y")
                file_name = f"Balayage_{hh}.txt"
                os.makedirs(save_path, exist_ok=True)
                full_path = os.path.join(save_path, file_name)
                with open(full_path, 'w') as f:
                    header = ["Frequency (Hz)"]
                    for trace in trace_name:
                        header.append(f"Magnitude_{trace}")
                        header.append(f"Phase_{trace}")
                    if state_avg:
                        header.append(f'{date}_{trace_name}_strat={start_freq/1E9}GHz_strop={stop_freq/1E9}GHz_average={count_avg}_[{x_val[hh-1]}_{y_val[hh-1]}]')
                    else:
                        header.append(f'{date}_{trace_name}_strat={start_freq/1E9}GHz_strop={stop_freq/1E9}GHz_[x_y]=[{x_val[hh-1]}_{y_val[hh-1]}]')
                    header.append(f'note=[{note}]')
                    f.write("\t".join(header) + "\n")
                    for l in range(points):
                        line = [f"{freq_data[l]:.2f}"]
                        for mag, phase in zip(all_magnitudes, all_phases):
                            line.append(f"{mag[l]:.4f}")
                            line.append(f"{phase[l]:.4f}")
                        f.write("\t".join(line) + "\n")
                print(f"Mesure {hh}/{int(nb_tot_position)}")
                hh = hh+1
                self.esp.write(f'{axis[1]}PR{str(pas_axe2)}') # when the axis 1 is at B[0] we need the axis 2 to move
                self.esp.write(f'{axis[1]}WS')
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
                        header.append(f'{date}_freq={freq_data[freq_idx]/1E9}GHz_lbd={299792458/freq_data[freq_idx]}m_xmin={A[0]}_xmax={B[0]}_y_min={A[1]}_ymax={B[1]}_stepx={pas_axe1}_stepy={pas_axe2}_average={count_avg}')
                    else:
                        header.append(f'{date}_freq={freq_data[freq_idx]/1E9}GHz_lbd={299792458/freq_data[freq_idx]}m_xmin={A[0]}_xmax={B[0]}_y_min={A[1]}_ymax={B[1]}_stepx={pas_axe1}_stepy={pas_axe2}')
                    header.append(f'note=[{note}]')
                    f.write("\t".join(header) + "\n")
                    for pos_idx in range(nb_tot_position):
                        line = [f"{x_val[pos_idx]:.3f}", f"{y_val[pos_idx]:.3f}"]
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
            # delete all "Balayage_i.txt" files
            ################################################################################################  
            motif = os.path.join(save_path, "Balayage_*.txt")
            fichiers = glob.glob(motif)
            for fichier in fichiers:
                os.remove(fichier)
            ################################################################################################
            # returning home, ask for error and closing connections
            ################################################################################################
            for axe in axis: 
                self.esp.write(f'{axe}PA0') # return to zero when the sweep is finished
                self.esp.write(f'{axe}WS')
            self.vna.close() 
            self.esp.close()
            print("Mesures terminées")
            print("Connexions fermées")
        except Exception as e:
            print(f"Erreur dans balayage_2D: {e}")
            try:
                for axe in axis:
                    self.esp.write(f'{axe}PA0') 
                    self.esp.write(f'{axe}WS')   
            except:
                pass
            try:
                self.vna.close()
                self.esp.close()
            except:
                pass
            raise  
            
    def rotation(self, trace_name=["S12","S21","S11","S22"], axis=1, units=7, theta_max=10, theta_min=0, sens="-to+", pas=1, state_avg=True, count_avg=5, save_path="C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad", note="", File_name="Compilation"):
        """
        Performs a full angular scan between two values of the θ angle θmin and θmax.
        The scan will begin at θmin and end at θmax. It will take measures at every step.

        Parameters
        ----------
        trace_name : array of string
            List of S-parameters . The default is ["S12","S21","S11","S22"].
        axis : integer
            ESP axis number. The default is 1.
        units : integer
            The unit of the movement (0 = encoder count, 1 = motor step, 2 = millimeter,
            3 = micrometer, 4 = inches, 5 = milli-inches, 6 = micro-inches, 7 = degree, 8 = gradient,
            9 = radian, 10 = milliradian, 11 = microradian). The default is 7.
        theta_max : integer or floating
            End coordinates of the scan. The default is 10.
        theta_min : integer or floating
            Start coordinates of the scan. The default is 0.
        sens : string
            Set the direction of the rotation of the motorized axis. The default is "-to+".
        pas : integer or floating
            Step size of the axis. The default is 1.
        state_avg : boolean
            If True the averaging will be on, if false it will be off. The default is True.
        count_avg : integer
            The number of measures to average on. The default is 5.
        save_path : string
            Output directory path. The default is "C:\\Users\\Thomas\\Documents\\Galaad_B\\vna_data_test_galaad".
        note : string
            Optional annotation. The default is "".
        File_name : string
            Name of the final files returned by the script. The default is "Compilation".

        Returns
        -------
        None.

        """
        try:
            ################################################################################################
            # parameters
            ################################################################################################
            channel = 1
            accel = "10"
            deccel = "10"
            speed = 3
            ################################################################################################
            # I don't know why the motion controller needs this (but it does)
            ################################################################################################
            self.esp.write_termination = '\r'
            self.esp.read_termination = '\r'
            ################################################################################################
            # give parameters to the axis (acceleration, speed mode...)
            ################################################################################################
            self.esp.write(f'{axis}MO')
            self.esp.write(f'{axis}SN{units}')
            self.esp.write(f'{axis}AC{accel}')
            self.esp.write(f'{axis}AG{deccel}')
            speed_mode = {1: "JW5", 2: "JH10", 3: "VU15"}[speed]
            self.esp.write(f'{axis}{speed_mode}')
            time.sleep(2)
            ################################################################################################
            # sweep spacial parameters
            ################################################################################################
            nb_tot_position = int(np.ceil(np.abs(1 + (theta_max - theta_min) / pas )))
            if sens == '-to+':
                sign = '+'
                theta_min_sign = theta_min
            elif sens == '+to-':
                sign = '-'
                theta_min_sign = -theta_min
            self.esp.write(f'{axis}PA{theta_min_sign}')
            self.esp.write(f'{axis}WS')
            time.sleep(3)
            start_freq = float(self.vna.query(f'SENSe{channel}:FREQuency:STARt?')) # ask the vna the value of start_freq
            stop_freq = float(self.vna.query(f'SENSe{channel}:FREQuency:STOP?')) # ask the vna the value of stop_freq
            points = int(self.vna.query(f'SENSe{channel}:SWEep:POINts?')) # ask the vna the number of point
            if start_freq == stop_freq:
                self.vna.write(f'SENSe{channel}:SWEep:POINts 1') # set the number of point to 1
                print("Balayage mono-fréquence:")
            unit = {0:"encoder_count", 1:"motor_step", 2:"mm", 3:"µm", 4:"inches", 5:"milli-inches", 6:"micro-inches", 7:"deg", 8:"grad", 9:"rad", 10:"mili-rad", 11:"µ-rad"}[int(units)]
            ################################################################################################
            # preset file creation
            ################################################################################################  
            file_name = f"{File_name}_parameters.txt"
            os.makedirs(save_path, exist_ok=True)    
            full_path = os.path.join(save_path, file_name)
            with open(full_path, 'w') as f:
                header = ["start_freq (Hz)", "stop_freq (Hz)", "number_of_point", "average", f"step ({unit})", f"theta_min ({unit})", f"theta_max ({unit})"]
                f.write("\t".join(header) + "\n")
                if state_avg:
                    line = [f"{start_freq}",  f"{stop_freq}", f"{points}", f"{count_avg}", f"{pas}", f"{theta_min}", f"{theta_max}"]
                else: 
                    line = [f"{start_freq}",  f"{stop_freq}", f"{points}", "0", f"{pas}", f"{theta_min}", f"{theta_max}"]
                f.write("\t".join(line) + "\n")
            ################################################################################################
            # this is the angular scan script
            ################################################################################################
            hh = 1 # hh tracks the number of measurements
            theta_val = np.arange(theta_min, theta_max + pas, pas)
            for i in range(nb_tot_position):
                if state_avg: # if state_avg=True: turn off and on the averaging before tacking the measure to make sure the averaging is done at a given position
                    self.vna.write(f'SENSe{channel}:AVERage OFF')
                    time.sleep(0.1)
                    self.vna.write(f'SENSe{channel}:AVERage ON')
                    time.sleep(1)
                    self.vna.write(f'SENSe{channel}:AVERage:COUNt {count_avg}') # set the average count to count_avg
                    for z in range(count_avg): # take count_avg measures to correctly average the signals
                        self.vna.write(f'INITiate{channel}:IMMediate')
                        self.vna.write('*WAI')
                else:
                    self.vna.write(f'SENSe{channel}:AVERage OFF')
                    self.vna.write(f'INITiate{channel}:IMMediate')
                    self.vna.write('*WAI')
                freq_data = np.linspace(start_freq, stop_freq, points)
                all_magnitudes = []
                all_phases = []
                for trace in trace_name:
                    self.vna.write(f'CALCulate{channel}:PARameter:SELect "{trace}"')
                    time.sleep(2)
                    self.vna.write(f'CALCulate{channel}:FORMat MLOG') # magnitude (dB)
                    time.sleep(2)
                    mag_data = self.vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA') # 'FDATA' -> real part of the data
                    self.vna.write(f'CALCulate{channel}:FORMat PHAS') # phase (°)
                    time.sleep(2)
                    phase_data = self.vna.query_ascii_values(f'CALCulate{channel}:DATA? FDATA')
                    all_magnitudes.append(mag_data)
                    all_phases.append(phase_data)
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
                        header.append(f'{date}_{trace_name}_freq={start_freq/1E9}GHz_average={count_avg}_theta={theta_val[hh-1]}')
                    else:
                        header.append(f'{date}_{trace_name}_freq={start_freq/1E9}GHz_theta={theta_val[hh-1]}')
                    header.append(f'note=[{note}]')                
                    f.write("\t".join(header) + "\n")
                    for l in range(points):
                        line = [f"{freq_data[l]:.2f}"]
                        for mag, phase in zip(all_magnitudes, all_phases):
                            line.append(f"{mag[l]:.4f}")
                            line.append(f"{phase[l]:.4f}")
                        f.write("\t".join(line) + "\n")
                print(f"Mesure {hh}/{int(nb_tot_position)}")
                if i < nb_tot_position - 1: # avoid macking too musch measurements
                    self.esp.write(f'{axis}PR{sign}{pas}')
                    self.esp.write(f'{axis}WS')
                    time.sleep(2)
                hh = hh+1
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
                    header.append(f'note=[{note}]')
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
            # delete all "Rotation_i.txt" files
            ################################################################################################  
            motif = os.path.join(save_path, "Rotation_*.txt")
            fichiers = glob.glob(motif)
            for fichier in fichiers:
                os.remove(fichier)
            ################################################################################################
            # returning home, ask for error and closing connections
            ################################################################################################
            self.esp.write(f'{axis}PA0')
            self.esp.write(f'{axis}WS')
            self.vna.close()
            self.esp.close()
            print("Mesures terminées\nConnexions fermées")
        except Exception as e:
            print(f"Erreur lors du balayage : {e}")
