# grupo3

## Integrantes:

| Nombre y Apellido  |      Mail                       |     usuario Gitlab    |
| ----------------   | ------------------------------- | ----------------------|
| Facundo Macia      | facuu.macia@gmail.com           |     facuu.macia       |
| Alejandro Aguilar  | alejandro_aguilar98@outlook.es  |     alejandro_aguilar |
| Martin Boglione    | martinboglione97@gmail.com      |     martinBoglione    |



----------------------------------------------------------------

## Entregas:


### Resumen de la Historia de los S.O: 

----------------------------------------------------------------
### Práctica 1: Aprobada

----------------------------------------------------------------
### Práctica 2: Aprobada

----------------------------------------------------------------
### Práctica 3 (pre entrega): CORRECCIONES PENDIENTES 


Kill
IO IN
IO OUT

A Corregir:
- https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L126
 No hay que hacer esto  aca (lo hace el _dispatcher.save()):  

 
 
-  https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L108
  Les esta faltando limpiar el setRunningPcb
  Que pasaria con el setRunningPcb si la readyQueue esta vacia luego de un Kill ?
  
  
- https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L156
  Estamos seguros que hay un proximo ??


  
-  https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L220
 deben preguntar por el RunningPcb (si es null, el CPU esta IDLE)
  
- https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L181
 deben preguntar por el RunningPcb (si es null, el CPU esta IDLE)

  
Sugerencia (no esta mal, solo les quedaria mas simple el codigo.. pueden aplicarlo en la P4, lo hablamos en clase)
  
  
- https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L105

 cambiar por: 

 ```
  killpcb.cambiarState("terminated") 
 ## Modifica el pc del pecb() con el pid dado y le asigna el pc de pcb() de la variable killpcb
 ## no es necesario (hecho en el _dispatcher.save()):         self.kernel._pcbTable.modificarPcPCB(killpcb.getPid(), killpcb.getPc())
```




----------------------------------------------------------------
### Práctica 3: Aprobada 


#### Correcciones: (lo pueden resolver directamente en la P4):

- IoInInterruptionHandler

Les falta limpiar el setRunningPcb

 https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L150

 ```
## Limpia la setRunningPcb
self.kernel._pcbTable.setRunningPcb(None)

 ```

#### Sugerencia

Estan repitiendo el cambio de estados (aca no pasa nada.. pero deberian dejar una sola de estas dos lineas, yo borraria "modificarStatePCB")

 ```
pcb.cambiarState("ready")
## Modifica el estado del pcb() en la _pcbTable() con en el _pid dado y le asigna "ready"
self.kernel._pcbTable.modificarStatePCB(pcb.getPid(), "ready")
 ```

 https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L117
 
 https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L160
 
 https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L146
 
 https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L182

 https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_3/so.py#L189
 




----------------------------------------------------------------
### Práctica 4: Aprobada (queda Gantt para revisar despues)

1. Timer reset:

hay que resetarlo en cada DISPATCHER.load(), en lugar de ponerlo en cada InterruptionHandler (HARDWARE.timer.reset())

- https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_4/so.py#L118
- https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_4/so.py#L156

- la unica que esta bien es la de TimeoutInterruptionHandler (pero si ya lo hace el DISPATCHER.load, solo lo deberiamos hacer en el ELSE del if




2.  Que pasa con el pcbRunning aca donde quedo despues de la expropiacion?

https://gitlab.com/2023-s1_3/grupo3/-/blob/main/practica_4/so.py#L219

(en IoOutInterruptionHandler lo tienen bien, es un problema que se genera por la duplicacion del codigo... podrian refactorizar esto en un metodo unico en AbstractInterruptionHandler)


3. Gantt
 lo revisamos en clase ??



4. Aging:OK
