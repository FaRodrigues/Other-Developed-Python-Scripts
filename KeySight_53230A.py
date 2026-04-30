# -*- coding: utf-8 -*-
# Author: Fernando A. Rodrigues
# Company: Inmetro

# 2-channel time interval measurement example
# // use CONFigure to set up a 2-channel time interval
# // measurement - start on ch. 1, stop on ch. 2
import math
import time
from collections import deque

import numpy as np
import pyvisa
from quantiphy import Quantity

rm = pyvisa.ResourceManager()
recursos = rm.list_resources()
print(f"Visa Interfaces Found: {recursos}")

inst = rm.open_resource('USB0::0x0957::0x1907::MY61090273::0::INSTR')

dequetowrite = deque([])
dequetoread = deque([])

singlechannel = False

if singlechannel:

    '''
    Notes:
    1 - Input coupling and impedance are set to assure the intended start and stop trigger 
    thresholds as the thresholds are specified as absolute values. The measurement starts 
    on the positive (rising) edge on channel 1, and stops on the negative (falling) edge.
    '''

    dequetowrite.append("*RST")  # reset to start from known state
    dequetowrite.append("CONF:TINT (@1)")  # ''' configure 1-ch measurement '''
    dequetowrite.append("INP:COUP AC")
    dequetowrite.append("INP:IMP 50")
    dequetowrite.append("INP:LEV1 1.0")
    dequetowrite.append("INP:LEV2 1.0")
    dequetowrite.append("INP:SLOP1 POS")  # set start slope to positive (rising)
    dequetowrite.append("INP:SLOP2 NEG")  # set stop slope to negative (falling)

else:

    '''
    Notes:

    1 - Auto-level is enabled on both channels to specify relative 
    threshold levels of 10% of the peak-to-peak signal level. 
    The measurement starts on a positive (rising) edge on channel 1, and stops on a positive edge on channel 2. 

    2  - A gate stop hold off is specified to select the desired rising edge on channel 2 and, 
    therefore, the interval to be measured.
    '''

    dequetowrite.append("*RST")  # reset to start from known state
    dequetowrite.append("SYST:TIM 5")  # set a 5s measurement timeout
    dequetowrite.append("CONF:TINT (@1), (@2)")  # ''' configure 2-ch measurement '''
    dequetowrite.append("INP1:LEV:AUTO ON")
    dequetowrite.append("INP2:LEV:AUTO ON")
    dequetowrite.append("INP1:LEV1 1.0")
    dequetowrite.append("INP2:LEV1 1.0")
    dequetowrite.append("INP1:SLOP POS")
    dequetowrite.append("INP2:SLOP POS")
    dequetowrite.append("INP1:IMP 50")
    dequetowrite.append("INP2:IMP 50")
    dequetowrite.append("INP1:COUP DC")
    dequetowrite.append("INP2:COUP DC")
    dequetowrite.append("INP1:NREJ ON")
    dequetowrite.append("INP2:NREJ ON")

    dequetowrite.append("SENS:GATE:STOP:HOLD:SOUR TIME")
    # dequetowrite.append("SENS:GATE:STOP:HOLD:TIME 2E-9")
    dequetowrite.append("SENS:GATE:STAR:SOUR IMM")
    dequetowrite.append("SENS:GATE:STOP:SOUR IMM")
    dequetowrite.append("SENS:TINT:GATE:SOUR IMM")

for comando in dequetowrite:
    print(comando)
    time.sleep(0.1)
    inst.write(comando)

dequetoread.append("READ?")

delaylist = []
contador = 0


# respquery = inst.query("READ?")

for comando in dequetoread:
    for x in range(200):
        contador += 1
        respquery = inst.query(comando)
        delay = np.double(str(respquery).replace("\n", ""))
        delaylist.append(delay)
        print(f"{contador} | Delay = {Quantity(delay, 's')}")
        time.sleep(1)

tipomedida = "DeltaT{}".format("1")

media = Quantity(np.double(np.mean(delaylist)), 's')
mediana = Quantity(np.double(np.median(delaylist)), 's')

stdvalue = Quantity(np.double(np.std(np.array(delaylist))), 's')
stduncertainty = Quantity(np.divide(stdvalue, np.sqrt(len(delaylist))), 's')
# stduncertainty = Quantity(np.divide(stdvalue, np.sqrt(len(delaylist))), 's')
filename = f"delay_{tipomedida}.txt"
with open(filename, 'w') as f:
    f.write(f"\nMeasured Values = {delaylist} \nMean = {media}\nMedian = {mediana}\nStandard Deviation = {stdvalue}\nUncertainty = {stduncertainty}\n")

print(f"Measured Values = {delaylist}\nStandard Deviation = {stdvalue}")
print(f"Media = {media}")
print(f"Median = {mediana}")
print(f"Standard Uncertainty = {stduncertainty}")
print(f"Measured values stored in file: {filename}")