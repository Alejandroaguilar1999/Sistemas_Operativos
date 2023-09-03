#!/usr/bin/env python

from hardware import *
import log
import heapq


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

    def expropiate(self, pcbRunning, pcb):
        self.kernel._dispatcher.save(pcbRunning)
        pcbRunning.cambiarState("ready")
        self.kernel._scheduler.add(pcbRunning)
        self.kernel._pcbTable.setRunningPcb(pcb)
        pcb.cambiarState("running")
        self.kernel._dispatcher.load(pcb)
    
    def pcbRunning(self, pcb):
        pcb.cambiarState("running")
        self.kernel._pcbTable.setRunningPcb(pcb)
        self.kernel._dispatcher.load(pcb)


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):

        killpcb = self.kernel._pcbTable.getRunningPcb()
        self.kernel._dispatcher.save(killpcb)
        killpcb.cambiarState("terminated")
        self.kernel._pcbTable.setRunningPcb(None)

        ## Consultado el estado del _arrayPCB en la _readyQueue()
        if (self.kernel._scheduler.NotIsEmpty()):

            ## Obtiene el proximo pcb() de la _arrayPCB en la _readyQueue() siguiendo la metodologia FIFO
            newPCB = self.kernel._scheduler.getNext()
            ## Modifica el estado del pcb() asignado a la variable newPCB a "ready"
            newPCB.cambiarState("running")
            ##  Carga pcb() de la variable newPCB en el CPU()
            self.kernel._dispatcher.load(newPCB)
            ##
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
        pcb = self.kernel._pcbTable.getRunningPcb()
        ## Salava el pc del cpu() y se lo asigna al pcb() almacenado en la variable pcb
        self.kernel._dispatcher.save(pcb)
        ## Cambia el _state del pcb() asignado a la variable pcb a "waiting"
        pcb.cambiarState("waiting")
        ##
        self.kernel._pcbTable.setRunningPcb(None)

        ## Delega el manejo del pcb() asignado a la variable pcb al ioDeviceController()
        self.kernel.ioDeviceController.runOperation(pcb, operation)

        ## Consulta el estado del _arrayPcb en la _readyQueue
        if (self.kernel._scheduler.NotIsEmpty()):
            ## Obtiene el proximo pcb() de la _readyQueue y lo asigna a la variable newPCB
            newPCB = self.kernel._scheduler.getNext()
            ## Cambia el _state del pcb() asignado a la variable newPCB a "waiting"
            newPCB.cambiarState("running")
            ##
            self.kernel._pcbTable.setRunningPcb(newPCB)
            ## Carga el pcb() asignado a la variable newPCB en el cpu()
            self.kernel._dispatcher.load(newPCB)

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())


class IoOutInterruptionHandler(AbstractInterruptionHandler):
    
    def execute(self, irq):
        ## Obtiene el pcb() de la salida del ioDeviceController() y lo asigna a la variable pcb
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        pcbRunning = self.kernel._pcbTable.getRunningPcb()

        if(pcbRunning == None):
            ## Cambia El estado del pcb a "running" y lo carga en el CPU()
            self.pcbRunning(pcb)
        elif (self.kernel._scheduler.mustExpropiate(pcbRunning, pcb)):
            self.expropiate(pcbRunning, pcb)
        else:
            ## Modifica el estado del pcb() asignado a la variable pcb a "ready"
            pcb.cambiarState("ready")
            ## Almacena el pcb() de la variable pcb en la _arrayPCB de la _readyQueue()
            self.kernel._scheduler.add(pcb)

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())


#* PRACTICA 3
class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        parameters = irq.parameters
        program = parameters['program']
        priority = parameters['priority']

        ## Crea un nuevo PCB() - le asigna un pid unico y lo inicia con el estado en "new"
        pcb = PCB(self.kernel._pcbTable.getNewPID(), 0, 0, "new", priority)
        ## Carga los parametros en memoria
        baseDir = self.kernel._loader.load_program(program)
        ## Le asigna una _baseDir y cambia el estado a "ready"
        pcb.modificaBaseDir(baseDir)
        pcb.cambiarState("ready")

        pcbRunning = self.kernel._pcbTable.getRunningPcb()

        ## Consulta el estado del cpu
        if(pcbRunning == None):
            ## Cambia El estado del pcb a "running" y lo carga en el CPU()
            self.pcbRunning(pcb)
        elif (self.kernel._scheduler.mustExpropiate(pcbRunning, pcb)):
            self.expropiate(pcbRunning, pcb)
        else:
            self.kernel._scheduler.add(pcb)
        
        ## Almacena el pcb en la PCB_TABLE()
        self.kernel._pcbTable.add(pcb)

        ## Imprime el estado del _pcbTable
        log.logger.info(self.kernel._pcbTable.__repr__())


class StatInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        self.kernel._scheduler.checkTick()
        # self.kernel._diagramaDeGantt.activateGantt()
        # self.kernel._diagramaDeGantt.hacerGantt()


class TimeoutInterruptionHandler(AbstractInterruptionHandler):
    
    def execute(self, irq):
        if self.kernel._scheduler.NotIsEmpty():
            pcbRunning = self.kernel._pcbTable.getRunningPcb()
            newPcb = self.kernel._scheduler.getNext()
            self.expropiate(pcbRunning, newPcb)

        log.logger.info(self.kernel._pcbTable.__repr__())


#* Creacion el Object LOADER()
class LOADER():
    
    def __init__(self):
        self._baseDir = 0

    ## Carga el prograa dado en memoria
    def load_program(self, program):
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
        self._runningPcb = None

    ## Retorna el pcb con el pid proporsionado 
    def get(self, pid):
        for index in self._table:
            if pid == index.getPid():
                return index
    
    def setRunningPcb(self, arg):
        self._runningPcb = arg

    ## Retorna el pcb() que tiene el estado "running"
    def getRunningPcb(self):
        return self._runningPcb
    
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
    
    def __repr__(self):
        listaPcb = []
        for elem in self._table:
            listaPcb.append(elem.__repr__())
        
        return listaPcb
    


#* Creacion el Object PCB()
class PCB():

    def __init__(self, pid, baseDir, pc, state, prioridad):
        self._pid = pid
        self._baseDir = baseDir 
        self._pc = pc
        self._state = state 
        self._prioridad = prioridad

    def getTick(self):
        return self._tickIng
    
    def setTick(self, nuevoTick):
        self._tickIng = nuevoTick

    def getPid(self):
        return self._pid
    
    def getPriority(self):
        return self._prioridad
     
    def getPc(self):
        return self._pc
     
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


class ABSTRACT_SCHEDULER():

    def __init__(self):
        pass

    def add(self, pcb):
        pass

    def getNext(self):
        pass

    def NotIsEmpty(self):
        pass

    def mustExpropiate(self, pcb_1, pcb_2):
        return False

    def checkTick(self):
        pass


class SCHEDULER_FCFS(ABSTRACT_SCHEDULER):
    
    def __init__(self):
        self._readyQueue = []
    
    def add(self, pcb):
        self._readyQueue.append(pcb)
    
    def getNext(self):
        pcb = self._readyQueue.pop(0)
        return pcb
    
    def NotIsEmpty(self):
        return bool(self._readyQueue)
    
class SCHEDULER_PRIORIDAD_NO_EXP(ABSTRACT_SCHEDULER):
     
    def __init__(self):
        self._readyQueue = [[], [], [], [], []]
        self.tickToAge = 3
    
    def checkTick(self):
        if self.tickToAge == 0:
            self.timeToAge()
            self.tickToAge = 3
        else:
            self.tickToAge -= 1
    
    def timeToAge(self):
        cont = 1
        while (cont < 5):
            self.envejecer(self._readyQueue[cont], self._readyQueue[cont-1])
            cont += 1
    
    def envejecer(self, arr, poner):
        while bool(arr) and (3 + arr[0]['tick'] <= HARDWARE.clock.currentTick):
            arr[0]['priority'] -= 1
            poner.append(arr.pop(0))  
    
    def add(self, pcb):
        priority = pcb.getPriority()
        psItem = {'tick': HARDWARE.clock.currentTick, 'pcb': pcb, 'priority': priority}
        self._readyQueue[priority - 1].append(psItem)

    def getNext(self):
        for index in self._readyQueue:
            if bool(index):
                return index.pop(0)['pcb']
    
    def NotIsEmpty(self):
        return (bool(self._readyQueue[0]) or bool(self._readyQueue[1]) 
                or bool(self._readyQueue[2]) or bool(self._readyQueue[3]) or bool(self._readyQueue[4]))
    

class SCHEDULER_PRIORIDAD_EXP(SCHEDULER_PRIORIDAD_NO_EXP):
    
    def mustExpropiate(self, pcb_1, pcb_2):
        return pcb_1.getPriority() > pcb_2.getPriority()

class SCHEDULER_RR(SCHEDULER_FCFS):
    
    def __init__(self):
        super().__init__()
        self.setearTimer(3)
    
    def setearTimer(self, quantum):
        HARDWARE.timer.quantum = quantum
        # HARDWARE.timer._active = True

class DIAGRAMA_DE_GANTT(): 

    def __init__(self, pcbTable):
        self._pcbTable = pcbTable
        self._copiaPcbTable = []
        self._headers = []
        self._isActive = False # por default esta desactivado

    def getIsActive(self):
        return self._isActive
    
    def getCopiaPcbTable(self):
        return self._copiaPcbTable
    
    def getHeaders(self):
        return self._headers

    ## Indica si todos los PCB terminaron, osea, su State es "terminated"
    def allTerminated(self):
        for pcb in self._pcbTable._table:
            if pcb._state != "terminated":
                return False
        return True
    
    ## Guarda el state de cada PCB por cada tick
    def tickInformation(self):
        arrayPorTick = []
        for pcb in self._pcbTable._table:
            arrayPorTick.append(pcb._state) ## Guarda todos los PCB en ese tick en un array
            self._copiaPcbTable.append(arrayPorTick) ## Guarda ese array en otro array para que quede un array para cada tick

    def printGantt(self):     
        print(tabulate(self.mapGantt(), tablefmt = 'fancy_grid', showindex = True, headers = self.headersGantt()))

    def activateGantt(self):
        self._isActive = True

    def desactivateGantt(self):
        self._isActive = False

    # Esto es para que en la primer columna de la tabla se impriman todos los elementos del primer array
    def transposedArray(self):
        return list(map(list, zip(*self.getCopiaPcbTable())))

    # Devuelve el indice de cada sub array en copiaPcbTable
    def headersGantt(self):
        for index, sublist in enumerate(self.getCopiaPcbTable()):
            self._headers.append(index)
        return self._headers

    # Devuelve un nuevo array donde "Terminated" es "T", "Ready" es ".", "Running" es "R" y "Waiting" es "W"
    def mapGantt(self): 
        transformedArray = list(map(lambda sublist: ["T" if item == "terminated" else "." if item == "ready" else "W" if item == "waiting" else "R" for item in sublist], self.transposedArray()))
        return transformedArray

    def hacerGantt(self):
        self.tickInformation()
        if(self.getIsActive() and self.allTerminated()):
            self.printGantt()
            self.desactivateGantt()


#* Creacion el Object DISPATCHER()
class DISPATCHER():
    
    ## Carga el pcb() dado en la CPU()
    def load(self, pcb):
        HARDWARE.cpu.pc = pcb.getPc()
        HARDWARE.mmu.baseDir = pcb.getBaseDir()
        HARDWARE.timer.reset()

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

        newHandler = NewInterruptionHandler(self) 
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        #Tp 4
        statHandler = StatInterruptionHandler(self) 
        HARDWARE.interruptVector.register(STAT_INTERRUPTION_TYPE, statHandler)

        timeoutHandler = TimeoutInterruptionHandler(self)
        HARDWARE.interruptVector.register(TIMEOUT_INTERRUPTION_TYPE, timeoutHandler)
        
        HARDWARE.cpu.enable_stats = True
        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)

        self._loader = LOADER()
        self._pcbTable = PCB_TABLE()
        self._dispatcher = DISPATCHER()
        self._diagramaDeGantt = DIAGRAMA_DE_GANTT(self._pcbTable)
        
        #self._scheduler = SCHEDULER_FCFS()
        #self._scheduler = SCHEDULER_PRIORIDAD_NO_EXP()
        #self._scheduler = SCHEDULER_PRIORIDAD_EXP()
        self._scheduler = SCHEDULER_RR()
        
        #HARDWARE.cpu.enable_stats = True

    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    def run(self, program, priority = None):
        parameters = {'program': program, 'priority': priority}
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, parameters)
        HARDWARE.interruptVector.handle(newIRQ)

        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)


    def __repr__(self):
        return "Kernel "
