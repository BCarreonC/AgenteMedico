# Funciones nuevas del agente

## Intenciones

```text
list_appointments
cancel_appointment
reschedule_appointment
confirm_appointment
complete_appointment
mark_appointment_no_show
```

## Ejemplos

```text
Muéstrame las citas de Juan Pérez
¿Qué citas tiene la doctora Ana mañana?
¿Cuáles son las citas pendientes de hoy?
Cancela la cita de Juan Pérez con Ana López del 30 de julio
Reprograma la cita con ID 66... para el 4 de agosto a las 12:00
Confirma la cita con ID 66...
Marca como atendida la cita con ID 66...
El paciente no se presentó a la cita con ID 66...
```

Cuando una operación encuentra varias citas, el agente no selecciona una arbitrariamente. Devuelve las coincidencias y solicita el ID o una fecha/hora más precisa.

## Archivos principales modificados

```text
app/prompts/system_prompt.py
app/nodes/planner.py
app/nodes/router.py
app/nodes/responder.py
app/services/nest_api.py
app/tools/appointments.py
```

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas mediante `/chat` están en `tests/manual`.
