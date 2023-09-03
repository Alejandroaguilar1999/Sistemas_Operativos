#!/usr/bin/env python

from hardware import *
import log


## emulates a compiled program
class Program():

    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController():

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            #print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb

            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)

## emulates the  Interruptions Handlers
class AbstractInterruptionHandler():
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))



class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):

        ## Obtiene el pcb() de la salida del IoDeviceController() y se lo asigna a la variable killpcb
        killpcb = self.kernel._pcbTable.getRunningPCB()
        ## Salva el pc del cpu() en el pcb() asignado a la variable killpcb
        self.kernel._dispatcher.save(killpcb)
        ## Modifica el estado del pcb() con el pid dado en la _psbTable() y le asigna "terminated"
        self.kernel._pcbTable.modificarStatePCB(killpcb.getPid(), "terminated")
        ## Modifica el pc del pecb() con el pid dado y le asigna el pc de pcb() de la variable killpcb
        self.kernel._pcbTable.modificarPcPCB(killpcb.getPid(), killpcb.getPc())
        ## Limpia la setRunningPcb
        self.kernel._pcbTable.setRunningPcb(None)

        ## Consultado el estado del _arrayPCB en la _readyQueue()
        if (self.kernel._readyQueue.arrayPCB_NotEmpty()):

            ## Obtiene el proximo pcb() de la _arrayPCB en la _readyQueue() siguiendo la metodologia FIFO
            newPCB = self.kernel._readyQueue.devolverProximo()
            ## Modifica el estado del pcb() asignado a la variable newPCB a "ready"
            newPCB.cambiarState("running")
            ## Modifica el _pc del pcb() con el pid dado en la _pcbTable() y le asigna el _pc de la variable pcb 
            self.kernel._pcbTable.modificarPcPCB(newPCB.getPid(), newPCB.getPc())
            ## Modifica el state del pcb() con el pid dado en la _pcbTable() y le asigna "running"
            self.kernel._pcbTable.modificarStatePCB(newPCB.getPid(), "running")
            ##  Carga pcb() de la variable newPCB en el CPU()
            self.kernel._dispatcher.load(newPCB)

            self.kernel._pcbTable.setRunningPcb(newPCB)

        ## Imprim iprime el aviso de programa finalizado
        log.logger.info(" Program Finished ")

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())
    


class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        ##
        operation = irq.parameters

        ## Obtiene el pcb() que tiene el _state "running" de la _pcbTable() y lo asigna a una variable 
        pcb = self.kernel._pcbTable.getRunningPCB()
        ## Salava el pc del cpu() y se lo asigna al pcb() almacenado en la variable pcb
        self.kernel._dispatcher.save(pcb)
        ## Cambia el _state del pcb() asignado a la variable pcb a "waiting"
        pcb.cambiarState("waiting")
        ## Modifica el _pc del pcb() con el pid dado en la _pcbTable() y le asigna el _pc de la variable pcb 
        self.kernel._pcbTable.modificarPcPCB(pcb.getPid(), pcb.getPc())
        ## Modifica el state del pcb() con el pid dado en la _pcbTable() y le asigna "waiting"
        self.kernel._pcbTable.modificarStatePCB(pcb.getPid(), "waiting")

        ## Delega el manejo del pcb() asignado a la variable pcb al ioDeviceController()
        self.kernel.ioDeviceController.runOperation(pcb, operation)

        ## Consulta el estado del _arrayPcb en la _readyQueue
        if (self.kernel._readyQueue.arrayPCB_NotEmpty()):
            ## Obtiene el proximo pcb() de la _readyQueue y lo asigna a la variable newPCB
            newPCB = self.kernel._readyQueue.devolverProximo()
            ## Cambia el _state del pcb() asignado a la variable newPCB a "waiting"
            newPCB.cambiarState("running")
            ## Modifica el state del pcb() con el pid dado en la _pcbTable() y le asigna "running"
            self.kernel._pcbTable.modificarStatePCB(newPCB.getPid(), "running")
            self.kernel._pcbTable.setRunningPcb(newPCB)
            ## Carga el pcb() asignado a la variable newPCB en el cpu()
            self.kernel._dispatcher.load(newPCB)
            
        ## Imprime el estado del ioDeviceController()
        #log.logger.info(self.kernel.ioDeviceController)

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        ## Obtiene el pcb() de la salida del ioDeviceController() y lo asigna a la variable pcb
        pcb = self.kernel.ioDeviceController.getFinishedPCB()

        if(self.kernel._pcbTable.getRunningPCB() == None):
            ## Cambia El estado del pcb a "running" y lo carga en el CPU()
            pcb.cambiarState("running")
            self.kernel._dispatcher.load(pcb)
            ## Modifica el estado del pcb() en la _pcbTable() con en el _pid dado y le asigna "running"
            self.kernel._pcbTable.modificarStatePCB(pcb.getPid(), "running")
            self.kernel._pcbTable.setRunningPcb(pcb)
        else:
            ## Modifica el estado del pcb() asignado a la variable pcb a "ready"
            pcb.cambiarState("ready")
            ## Modifica el estado del pcb() en la _pcbTable() con en el _pid dado y le asigna "ready"
            self.kernel._pcbTable.modificarStatePCB(pcb.getPid(), "ready")
            ## Almacena el pcb() de la variable pcb en la _arrayPCB de la _readyQueue()
            self.kernel._readyQueue.agregarAReadyQueue(pcb)

        ## Modifica el pc del pcb() en la _pcbTable() con el _pid dado y le asigna el _pc de el pcb() en la variable pcb
        self.kernel._pcbTable.modificarPcPCB(pcb.getPid(), pcb.getPc())

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())


#* PRACTICA 3
class NewInterruptionHandler(AbstractInterruptionHandler):
    #crea un nuevo PCB
    #lo "carga" en la PCB Table
    #llama al LOADER para hacer LOADER.load(program)
    def execute(self, irq):
        ##
        program = irq.parameters
        ## Crea un nuevo PCB() - le asigna un pid unico y lo inicia con el estado en "new"
        pcb = PCB(self.kernel._pcbTable.getNewPID(), 0, 0, "new")
        ## Carga los parametros en memoria
        baseDir = self.kernel._loader.load_program(program)
        ## Le asigna una _baseDir y cambia el estado a "ready"
        pcb.modificaBaseDir(baseDir)
        pcb.cambiarState("ready")

        ## Consulta el estado del cpu
        if(self.kernel._pcbTable.getRunningPCB() == None):
            ## Cambia El estado del pcb a "running" y lo carga en el CPU()
            pcb.cambiarState("running")
            self.kernel._pcbTable.setRunningPcb(pcb)
            self.kernel._dispatcher.load(pcb)
        else:
            ## Almacena el pcb en la READY_QUEUE()
            self.kernel._readyQueue.agregarAReadyQueue(pcb)
        
        ## Almacena el pcb en la PCB_TABLE()
        self.kernel._pcbTable.add(pcb)

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())
        

#* Creacion el Object LOADER()
class LOADER():
    
    def __init__(self):
        self._baseDir = 0

    ## Carga el prograa dado en memoria
    def load_program(self, program):
        ## 
        progSize = len(program.instructions)
        for index in range(0, progSize):
            inst = program.instructions[index]
            HARDWARE.memory.write(self._baseDir, inst)
            self._baseDir += 1
        return self._baseDir - progSize


#* Creacion el Object PCB_TABLE()
class PCB_TABLE():

    def __init__(self):
        self._table = []
        self._ruuningPcb = None

    ## Retorna el pcb con el pid proporsionado 
    def get(self, pid):
        for index in self._table:
            if pid == index.getPid():
                return index

    ##       
    def setRunningPcb(self, arg):
        self._ruuningPcb = arg

    ## Retorna el pcb() que tiene el estado "running"
    def getRunningPCB(self):
        return self._ruuningPcb
    
    ## Agrega un pcb a table
    def add(self, pcb):
        self._table.append(pcb)

    ## elimina el PCB con ese PID de la tabla 
    def remove(self, pid):
        varTem = []
        for index in self._table:
            if pid != index.getPid():
                varTem.extend([index])
        self._table = varTem

    ## Crea un _pid unico y lo retorna
    def getNewPID(self):
        if len(self._table) == 0:
            return 1
        else:
            return self._table[-1].getPid() + 1
   
    ## Modifica el _state del pcb() que tiene el pid suministrado 
    def modificarStatePCB(self, pid, state):
        for index in self._table:
            if pid == index.getPid():
                index.cambiarState(state)
                break
    ## Modifica el _pc del pcb() que tiene el pid suministrado
    def modificarPcPCB(self, pid, pc):
        for index in self._table:
            if pid == index.getPid():
                index.cambiarPc(pc)
                break
    
    def __repr__(self):
        listaPcb = []
        for elem in self._table:
            listaPcb.append(elem.__repr__())
        
        return listaPcb

#* Creacion el Object PCB()
class PCB():

    def __init__(self, pid, baseDir, pc, state):
        self._pid = pid
        self._baseDir = baseDir 
        self._pc = pc
        self._state = state 
    
    def getPid(self):
        return self._pid

    ## 
    def getPc(self):
        return self._pc

    ## 
    def getBaseDir(self):
        return self._baseDir

    ## Cabia el _pc del PCB() y le asigna pc
    def cambiarPc(self, pc):
        self._pc = pc

    ## Cabia el _state del PCB() y le asigna state
    def cambiarState(self, state):
        self._state = state

    ## Cabia el _baseDir del PCB() y le asigna bDir
    def modificaBaseDir(self, bDir):
        self._baseDir = bDir
    
    def __repr__(self):
        ##return "HARDWARE state {cpu}\n{mem}".format(cpu=self._cpu, mem=self._state)
        return "PID {pid}, State: {state}".format(pid=self._pid, state=self._state)
        


#* Creacion el Object READY_QUEUE()
class READY_QUEUE():
        
        def __init__(self):
            self._arrayPCB = []

        ## Agregar el pcb() suministrado al _arrayPCB 
        def agregarAReadyQueue(self, pcb) :
            self._arrayPCB.append(pcb)
        
        ## Retorna el proximo pcb en la _arrayPCB  siguiendo la etodologia FIFO
        def devolverProximo(self):
            pcb = self._arrayPCB.pop(0)
            return pcb

        ##
        def arrayPCB_NotEmpty(self):
            return len(self._arrayPCB) > 0


#* Creacion el Object DISPATCHER()
class DISPATCHER():
    
    ## Carga el pcb() dado en la CPU()
    def load(self, pcb):
        HARDWARE.cpu.pc = pcb.getPc()
        HARDWARE.mmu.baseDir = pcb.getBaseDir()

    ## Salva el estado de pc en un pcb() dado y pone el CPU() en IDLE
    def save(self, pcb):
        pcb.cambiarPc(HARDWARE.cpu.pc)
        HARDWARE.cpu.pc = -1


# emulates the core of an Operative System
class Kernel():

    def __init__(self):
        ## setup interruption handlers
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        #* PRACTICA 3
        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)

        self._loader = LOADER()
        self._pcbTable = PCB_TABLE()
        self._readyQueue = READY_QUEUE()
        self._dispatcher = DISPATCHER()
        


    @property
    def ioDeviceController(self):
        return self._ioDeviceController


    ## emulates a "system call" for programs execution
    def run(self, program):
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, program)
        HARDWARE.interruptVector.handle(newIRQ)
 
        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

        # set CPU program counter at program's first intruction
        #? Esto tendria que hacerlo el dispatcher?
        #HARDWARE.cpu.pc = 0


    def __repr__(self):
        return "Kernel "
