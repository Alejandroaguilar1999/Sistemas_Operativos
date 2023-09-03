from hardware import *
from so import *
import log


##
##  MAIN 
##
if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(40)


    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ##################
    prg1 = Program("prg1.exe", [ASM.CPU(2), ASM.IO()])
    prg2 = Program("prg2.exe", [ASM.CPU(2)])
    prg3 = Program("prg3.exe", [ASM.CPU(4), ASM.IO(), ASM.CPU(1)])
    prg4 = Program("prg4.exe", [ASM.CPU(3), ASM.IO(), ASM.CPU(1)])
    prg5 = Program("prg4.exe", [ASM.CPU(3), ASM.IO(), ASM.CPU(1)])
    # # execute all programs "concurrently"
    # kernel.run(prg1)
    # kernel.run(prg2)
    # kernel.run(prg3)

    # execute all programs
    kernel.run(prg5, 2)  ## 1 = prioridad del proceso
    kernel.run(prg4, 3)  ## 2 = prioridad del proceso
    kernel.run(prg3, 1)  ## 3 = prioridad del proceso
    #kernel.run(prg4, 4)  ## 3 = prioridad del proceso
    #kernel.run(prg5, 5)

    ## Switch on computer
    HARDWARE.switchOn()
    
