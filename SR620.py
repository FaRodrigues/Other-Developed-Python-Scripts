# -*- coding: utf-8 -*-
# Author: Fernando A. Rodrigues
# Company: Inmetro
# Adjusted by Luiz Paulo (LRTE - São Carlos)

"""
Automatic acquisition of measurements from the SR620 counter (Stanford Research Systems) via RS-232 interface with PyVISA.

Features:

- Automatic instrument configuration
- Discarding of initial measurements (stabilization)
- Measurements with timestamp
- Automatic saving to CSV
"""

import time
import csv
from datetime import datetime
from collections import deque

import numpy as np
import pyvisa
from quantiphy import Quantity

# ========================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ========================================

# Serial Port from SR620
# Example: 'ASRL/dev/ttyS0::INSTR' or 'ASRL/dev/ttyUSB0::INSTR'
porta_sr620 = 'ASRL/dev/ttyS0::INSTR'

# Name of output CSV file
arquivo_saida = "SR620_results.csv"

# Total number of measurements
num_medidas = 200

# Number of initial measurements to discard (stabilization)
descartar_iniciais = 3

# Number of internal points (affects waiting time)
numpoints_to_measure = 1

# Minimum waiting time between measurements (seconds)
tempo_espera_base = 0.6

rm = pyvisa.ResourceManager()
recursos = rm.list_resources()
print(f"Visa Interfaces Found: {recursos}")

try:
    inst = rm.open_resource(porta_sr620)
except Exception as e:
    print(f"Erro opening port {porta_sr620}: {e}")
    exit(1)

# Configurações típicas do SR620
inst.baud_rate = 9600
inst.data_bits = 8
inst.parity = pyvisa.constants.Parity.none
inst.stop_bits = pyvisa.constants.StopBits.one
inst.read_termination = '\n'
inst.write_termination = '\n'
inst.timeout = 10000  # 10 segundos

# ========================================
# CONFIGURAÇÃO DO INSTRUMENTO
# ========================================

dequetowrite = deque([
    "*RST",
    "AUTM 0",
    "MODE 0",       # 0 = Time Interval
    "CLCK 1",       # 1 = External clock
    "LEVL1, 1.0",
    "LEVL2, 1.0",
    "TSLP1, 0",
    "TSLP2, 0",
    "TERM1, 0",     # 0 = 50Ω
    "TERM2, 0",
    "TCPL1, 1",     # 1 = AC
    "TCPL2, 1",
    f"SIZE {numpoints_to_measure}",
    "SRCE 0",
    "ARMM 1"
])

print("\n🔧 Sending to SR620 configuration commands ...")
for comando in dequetowrite:
    print(f" -> {comando}")
    inst.write(comando)
    time.sleep(0.1)

# ========================================
# MEDIÇÕES DE ESTABILIZAÇÃO
# ========================================

if descartar_iniciais > 0:
    print(f"\nStarting {descartar_iniciais} stabilization measurements ...")
    for i in range(descartar_iniciais):
        inst.write("STRT")
        time.sleep(tempo_espera_base)
        try:
            _ = inst.query("XAVG?")
            print(f"   (Descartada) Medição de estabilização {i+1} concluída.")
        except Exception:
            print(f"Falha na medição de estabilização {i+1}. Ignorada.")
    print("Stabilization Done.\n")

# ========================================
# LOOP PRINCIPAL DE MEDIÇÃO
# ========================================

dequetorun = deque(["STRT", "DISP 0"])
medidalist = []

print("Starting main measurements...\n")

# Cria/limpa arquivo CSV e escreve cabeçalho
with open(arquivo_saida, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["# Measurement", "Timestamp", "Time (s)"])

    for contador in range(1, num_medidas + 1):
        print(f"Starting Measurement {contador}...")

        for comando in dequetorun:
            inst.write(comando)

        tempo_espera = max(tempo_espera_base, 0.4 * numpoints_to_measure)
        print(f"Waiting {tempo_espera:.1f} s to resume measurement...")
        time.sleep(tempo_espera)

        try:
            medida = inst.query("XAVG?").strip()
            valor = float(medida)
            medidalist.append(valor)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([contador, timestamp, valor])
            csvfile.flush()

            print(f"Measurement {contador}: {valor:.10e} s ({timestamp})")

        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([contador, timestamp, "Erro"])
            print(f"Error reading measurement {contador}: {e}")

        time.sleep(0.5)

# ========================================
# RESULTADOS FINAIS
# ========================================

if medidalist:
    mediana = np.median(medidalist)
    print(f"\nThe median of {len(medidalist)} valid measurements is = {Quantity(mediana, 's')}")
    print(f"Results stored if file: {arquivo_saida}")
else:
    print("\nNo valid measure was obtained.")

print("\nCompleted successfully.")