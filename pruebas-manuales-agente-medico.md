# Pruebas manuales del agente médico

Este documento contiene los casos de prueba manuales para validar las funciones de gestión de citas del agente médico.

## Datos de prueba sugeridos

- **Paciente:** Juan Pérez García
- **Médica:** Ana López
- **Fecha inicial:** 30 de julio de 2026
- **Hora inicial:** 10:30
- **Fecha de reprogramación:** 4 de agosto de 2026
- **Hora nueva:** 12:00
- **Duración:** 30 minutos

## Estados sugeridos para cada caso

Usa uno de los siguientes valores en el campo **Situación**:

- `No ejecutado`
- `En progreso`
- `Aprobado`
- `Fallido`
- `Bloqueado`

---

## Caso 1. Crear una cita base

**Situación:** `Aprobado`

**Prompt:**

> Agenda una cita para Juan Pérez García con la doctora Ana López el 30 de julio de 2026 a las 10:30 por 30 minutos. El motivo es control general.

**Resultado esperado:**

- La cita se crea correctamente.
- El estado inicial es `scheduled`.
- La fecha es `2026-07-30`.
- La hora es `10:30`.
- El agente devuelve o permite identificar el ID de la cita.

**Resultado obtenido:**

>  Aprobado.

**Observaciones:**

> Tarda alrededor de 10 a 15 segundos en contestar.

---

# Consultar citas

## Caso 2. Ver citas de un paciente

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las citas de Juan Pérez García.

**Resultado esperado:**

- El agente busca al paciente.
- Muestra sus citas.
- Debe aparecer la cita del 30 de julio de 2026 a las 10:30.

**Resultado obtenido:**

> Aprobado.

**Observaciones:**

> Pendiente.

---

## Caso 3. Ver citas de un médico

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las citas de la doctora Ana López.

**Resultado esperado:**

- El agente busca a la doctora Ana López.
- Muestra sus citas ordenadas por fecha.
- Debe aparecer la cita de Juan Pérez García.

**Resultado obtenido:**

> Aprobado.

**Observaciones:**

> Pendiente.

---

## Caso 4. Ver citas de un médico por fecha

**Situación:** `Aprobado`

**Prompt:**

> ¿Qué citas tiene la doctora Ana López el 30 de julio de 2026?

**Resultado esperado:**

- Solo aparecen citas de Ana López para esa fecha.
- Debe aparecer la cita de las 10:30.

**Resultado obtenido:**

> Aprobado.

**Observaciones:**

> Pendiente.

---

## Caso 5. Ver citas por fecha

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame todas las citas del 30 de julio de 2026.

**Resultado esperado:**

- El agente filtra las citas por fecha.
- Muestra todas las citas de ese día.

**Resultado obtenido:**

> Aprobado.

**Observaciones:**

> Pendiente.

---

## Caso 6. Ver citas programadas

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las citas programadas.

**Resultado esperado:**

- Solo aparecen citas con estado `scheduled`.

**Resultado obtenido:**

> Aprobado.

**Observaciones:**

> Pendiente.

---

## Caso 7. Ver citas confirmadas

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las citas confirmadas.

**Resultado esperado:**

- Solo aparecen citas con estado `confirmed`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 8. Ver citas canceladas

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las citas canceladas.

**Resultado esperado:**

- Solo aparecen citas con estado `cancelled`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 9. Ver citas pendientes de hoy

**Situación:** `Aprobado`

**Prompt:**

> ¿Cuáles son las citas pendientes de hoy?

**Resultado esperado:**

- El agente interpreta la fecha actual.
- Devuelve citas pendientes del día.
- Debe incluir las citas consideradas pendientes por la lógica del sistema.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 10. Ver próximas citas

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las próximas citas.

**Resultado esperado:**

- Solo aparecen citas futuras.
- Las citas están ordenadas desde la más próxima.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 11. Consulta combinada

**Situación:** `Aprobado`

**Prompt:**

> Muéstrame las citas programadas de Juan Pérez García del 30 de julio de 2026.

**Resultado esperado:**

El agente combina los filtros:

- Paciente.
- Fecha.
- Estado `scheduled`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

# Confirmar una cita

## Caso 12. Confirmar usando el ID

**Situación:** `No ejecutado`

**Precondición:**

- Contar con una cita en estado `scheduled`.
- Sustituir `[ID_CITA]` por el ID real.

**Prompt:**

> Confirma la cita con ID [ID_CITA].

**Resultado esperado:**

- El estado cambia de `scheduled` a `confirmed`.
- Se registra la fecha de confirmación, si el modelo la incluye.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 13. Confirmar usando información natural

**Situación:** `Aprobado`

**Prompt:**

> Confirma la cita de Juan Pérez García con la doctora Ana López del 30 de julio de 2026 a las 10:30.

**Resultado esperado:**

- El agente identifica una única cita.
- Cambia su estado a `confirmed`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 14. Confirmar una cita ya confirmada

**Situación:** `Error`

**Prompt:**

> Confirma nuevamente la cita de Juan Pérez García del 30 de julio de 2026 a las 10:30.

**Resultado esperado:**

- No se crea una cita nueva.
- El agente informa que ya está confirmada o que la transición no es necesaria.

**Resultado obtenido:**

> No encontré una cita que coincida con los datos proporcionados.

**Observaciones:**

> Pendiente.

---

# Reprogramar una cita

## Caso 15. Reprogramar usando el ID

**Situación:** `No ejecutado`

**Precondición:**

- Contar con una cita existente.
- Sustituir `[ID_CITA]` por el ID real.

**Prompt:**

> Reprograma la cita con ID [ID_CITA] para el 4 de agosto de 2026 a las 12:00 por 30 minutos.

**Resultado esperado:**

- La fecha anterior deja de ser la fecha activa de la cita.
- La cita cambia a `2026-08-04`.
- La hora cambia a `12:00`.
- El horario anterior queda libre.
- El horario nuevo queda ocupado.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 16. Reprogramar usando datos naturales

**Situación:** `Aprobado`

**Prompt:**

> Cambia la cita de Juan Pérez García con la doctora Ana López del 30 de julio de 2026 a las 10:30 para el 4 de agosto de 2026 a las 12:00.

**Resultado esperado:**

- El agente encuentra la cita anterior.
- Valida la disponibilidad del nuevo horario.
- Actualiza la fecha y la hora.
- Libera el horario anterior.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 17. Verificar la reprogramación

**Situación:** `No ejecutado`

**Prompt:**

> Muéstrame las citas de Juan Pérez García.

**Resultado esperado:**

- La cita activa ya no aparece el 30 de julio a las 10:30.
- La cita aparece el 4 de agosto a las 12:00.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 18. Verificar que el horario anterior quedó libre

**Situación:** `No ejecutado`

**Prompt:**

> Consulta la disponibilidad de la doctora Ana López el 30 de julio de 2026 para citas de 30 minutos.

**Resultado esperado:**

- El horario de las 10:30 vuelve a aparecer como disponible.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 19. Verificar que el horario nuevo quedó ocupado

**Situación:** `No ejecutado`

**Prompt:**

> Consulta la disponibilidad de la doctora Ana López el 4 de agosto de 2026 para citas de 30 minutos.

**Resultado esperado:**

- El horario de las 12:00 no aparece como disponible.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 20. Reprogramar hacia un horario ocupado

**Situación:** `No ejecutado`

**Precondición:**

- Debe existir una cita en el horario destino.

**Prompt:**

> Reprograma la cita con ID [ID_OTRA_CITA] para el 5 de agosto de 2026 a las 11:00.

**Resultado esperado:**

- La operación se rechaza.
- El agente informa que el horario no está disponible.
- La cita original conserva su fecha y hora.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

# Cancelar una cita

## Caso 21. Cancelar usando el ID

**Situación:** `No ejecutado`

**Prompt:**

> Cancela la cita con ID [ID_CITA]. El motivo es que el paciente no podrá asistir.

**Resultado esperado:**

- El estado cambia a `cancelled`.
- Se registra `cancellationReason`.
- Se registra `cancelledAt`.
- La cita no se elimina físicamente.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 22. Cancelar usando información natural

**Situación:** `No ejecutado`

**Prompt:**

> Cancela la cita de Juan Pérez García con la doctora Ana López del 4 de agosto de 2026 a las 12:00 porque el paciente no podrá asistir.

**Resultado esperado:**

- El agente localiza una única cita.
- Cambia el estado a `cancelled`.
- Conserva el registro en el historial.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 23. Verificar la cita cancelada

**Situación:** `No ejecutado`

**Prompt:**

> Muéstrame las citas canceladas de Juan Pérez García.

**Resultado esperado:**

- Aparece la cita cancelada.
- Se muestra el motivo de cancelación, cuando esté disponible.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 24. Verificar que el horario cancelado quedó libre

**Situación:** `No ejecutado`

**Prompt:**

> Consulta la disponibilidad de la doctora Ana López el 4 de agosto de 2026 para citas de 30 minutos.

**Resultado esperado:**

- El horario de las 12:00 vuelve a estar disponible.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 25. Cancelar una cita ya cancelada

**Situación:** `No ejecutado`

**Prompt:**

> Cancela nuevamente la cita con ID [ID_CITA_CANCELADA].

**Resultado esperado:**

- No se duplica la cancelación.
- El agente indica que la cita ya está cancelada o que la transición no es válida.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

# Completar una cita

## Caso 26. Crear una cita para completar

**Situación:** `No ejecutado`

**Prompt:**

> Agenda una cita para Juan Pérez García con la doctora Ana López el 6 de agosto de 2026 a las 10:00 por 30 minutos. El motivo es consulta de seguimiento.

**Resultado esperado:**

- La cita se crea con estado `scheduled`.
- Se obtiene el ID de la cita.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 27. Confirmar la cita que se completará

**Situación:** `No ejecutado`

**Prompt:**

> Confirma la cita con ID [ID_CITA_COMPLETAR].

**Resultado esperado:**

- El estado cambia a `confirmed`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 28. Marcar una cita como atendida

**Situación:** `No ejecutado`

**Prompt:**

> Marca como atendida la cita con ID [ID_CITA_COMPLETAR].

**Resultado esperado:**

- El estado cambia a `completed`.
- Se registra `completedAt`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 29. Consultar citas completadas

**Situación:** `No ejecutado`

**Prompt:**

> Muéstrame las citas completadas de Juan Pérez García.

**Resultado esperado:**

- Aparece la cita marcada como `completed`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 30. Intentar cancelar una cita completada

**Situación:** `No ejecutado`

**Prompt:**

> Cancela la cita con ID [ID_CITA_COMPLETAR].

**Resultado esperado:**

- La operación se rechaza.
- Una cita completada no cambia a `cancelled`.

**Resultado obtenido:**

> Marca que id no es valido cuando se intenta cancelar una cita completada

**Observaciones:**

> Pendiente.

---

# Marcar inasistencia

## Caso 31. Crear cita para probar inasistencia

**Situación:** `No ejecutado`

**Prompt:**

> Agenda una cita para Juan Pérez García con la doctora Ana López el 7 de agosto de 2026 a las 11:30 por 30 minutos. El motivo es revisión general.

**Resultado esperado:**

- La cita se crea correctamente.
- Se obtiene el ID de la cita.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 32. Marcar que el paciente no se presentó

**Situación:** `No ejecutado`

**Prompt:**

> El paciente no se presentó a la cita con ID [ID_CITA_NO_SHOW].

**Resultado esperado:**

- El estado cambia a `no_show`.
- Se registra `noShowAt`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

## Caso 33. Consultar inasistencias

**Situación:** `No ejecutado`

**Prompt:**

> Muéstrame las citas donde el paciente no se presentó.

**Resultado esperado:**

- Aparecen las citas con estado `no_show`.

**Resultado obtenido:**

> Pendiente.

**Observaciones:**

> Pendiente.

---

# Pruebas de ambigüedad

## Caso 34. Cancelar sin datos suficientes

**Situación:** `No ejecutado`

**Prompt:**

> Cancela la cita de Juan Pérez García.

**Resultado esperado:**

- Si hay varias coincidencias, el agente no elige una arbitrariamente.
- Solicita ID, fecha u hora.

**Resultado obtenido:**

> No encontré una cita que coincida con los datos proporcionados.[Cuando hay una cita agendada]

**Observaciones:**

> Pendiente.

---

## Caso 35. Reprogramar sin nueva fecha

**Situación:** `No ejecutado`

**Prompt:**

> Cambia la cita de Juan Pérez García con la doctora Ana López.

**Resultado esperado:**

- El agente solicita la nueva fecha.
- No modifica ninguna cita todavía.

**Resultado obtenido:**

> Falta la siguiente información: nueva fecha, nueva hora.

**Observaciones:**

> Pendiente.

---

## Caso 36. Reprogramar sin hora

**Situación:** `Fallo`

**Prompt:**

> Cambia la cita de Juan Pérez García para el 8 de agosto de 2026.

**Resultado esperado:**

- El agente solicita la nueva hora.
- No elige una hora automáticamente.

**Resultado obtenido:**

> Sin resultado entro en un bucle y no genero respuesta.

**Observaciones:**

> Se tarda demasiado 30 segundos

---

## Caso 37. Confirmar sin poder identificar la cita

**Situación:** `No ejecutado`

**Prompt:**

> Confirma la cita de Juan.

**Resultado esperado:**

- El agente solicita más información.
- No confirma una cita al azar.

**Resultado obtenido:**

> No encontré una cita que coincida con los datos proporcionados.

**Observaciones:**

> Pendiente.

---

# Pruebas de validación

## Caso 38. Intentar agendar en una fecha pasada

**Situación:** `No ejecutado`

**Prompt:**

> Agenda una cita para Juan Pérez García con la doctora Ana López el 27 de julio de 2026 a las 10:30 por 30 minutos.

**Resultado esperado:**

- La operación se rechaza porque la fecha ya pasó.

**Resultado obtenido:**

> Falta la siguiente información: motivo de la cita.

**Observaciones:**

> Pendiente.

---

## Caso 39. Intentar crear una cita duplicada

**Situación:** `No ejecutado`

**Prompt:**

> Agenda una cita para Juan Pérez García con la doctora Ana López el 7 de agosto de 2026 a las 10:30 por 30 minutos. El motivo es revisión.

**Procedimiento:**

1. Ejecutar el prompt una primera vez.
2. Ejecutar el mismo prompt nuevamente.

**Resultado esperado:**

- La primera cita se crea.
- La segunda operación se rechaza por conflicto de horario.

**Resultado obtenido:**

> La cita fue agendada correctamente.\n\nPaciente: Juan Pérez García\nMédico: Ana López\nFecha: 2026-08-07\nHorario: 10:30 a 11:00\nMotivo: revisión\nID de cita: 6a82ef3eb02487d143bce095

> El horario 10:30 no está disponible.\n\nHorarios disponibles:\n- 09:00 a 09:30\n- 09:30 a 10:00\n- 10:00 a 10:30\n- 11:00 a 11:30\n- 12:00 a 12:30\n- 12:30 a 13:00"

**Observaciones:**

> Pendiente.

---

## Caso 40. Duración inválida

**Situación:** `No ejecutado`

**Prompt:**

> Agenda una cita para Juan Pérez García con la doctora Ana López el 10 de agosto de 2026 a las 12:00 por 0 minutos. Motivo de la consulta: Revision general

**Resultado esperado:**

- La duración se rechaza.
- No se crea ninguna cita.

**Resultado obtenido:**

> La duración debe ser un número entre 15 y 240 minutos.

**Observaciones:**

> Pendiente.

---

## Caso 41. Médico inexistente

**Situación:** `No ejecutado`

**Prompt:**

> Muéstrame las citas del doctor Roberto Suarez.

**Resultado esperado:**

- El agente indica que no encontró al médico.
- No realiza la consulta con un ID vacío.

**Resultado obtenido:**

> No encontré un médico que coincida con «Roberto Suarez»

**Observaciones:**

> Pendiente.

---

## Caso 42. Paciente inexistente

**Situación:** `No ejecutado`

**Prompt:**

> Muéstrame las citas del Paciente Jose Martinez.

**Resultado esperado:**

- El agente indica que no encontró al paciente.

**Resultado obtenido:**

> No encontré un paciente que coincida con «Jose Martinez».

**Observaciones:**

> Pendiente.

---

# Pruebas conversacionales

Estas pruebas deben ejecutarse usando el mismo `session_id` [Puede ser un numero cualquiera 1].

## Caso 43. Cancelación en varios mensajes

**Situación:** `No ejecutado`

**Mensajes:**

1. > Muéstrame las citas de Juan Pérez García.
2. > Cancela la del 8 de agosto a las 10:30.
3. > El motivo es que el paciente estará fuera de la ciudad.

**Resultado esperado:**

- El agente conserva el contexto.
- Identifica la cita mostrada anteriormente.
- No cancela una cita distinta.

**Resultado obtenido:**

> [3er Prompt]Todavía no puedo realizar esa operación. Puedo buscar pacientes y administrar citas del consultorio

**Observaciones:**

> Pendiente.

---

## Caso 44. Reprogramación en varios mensajes

**Situación:** `No ejecutado`

**Mensajes:**

1. > Quiero cambiar una cita de Juan Pérez García.
2. > La que tiene con Ana López.
3. > Es la del 7 de agosto a las 10:30.
4. > Muévela al 10 de agosto a las 12:30.

**Resultado esperado:**

- El agente conserva paciente, médica, fecha y hora entre mensajes.
- La cita se reprograma al horario indicado.
- El horario anterior queda libre.

**Resultado obtenido:**

> [1er prompt] Falta la siguiente información: nueva fecha, nueva hora.
> [3er Prompt] Todavía no puedo realizar esa operación. Puedo buscar pacientes y administrar citas del consultorio
> [4to Prompt] Falta la siguiente información: ID de la cita o datos para localizarla (paciente, médico, fecha u hora).

**Observaciones:**

> Pendiente.

---

# Resumen de ejecución

| Caso | Descripción | Situación |
|---:|---|---|
| 1 | Crear cita base | No ejecutado |
| 2 | Ver citas de paciente | No ejecutado |
| 3 | Ver citas de médico | No ejecutado |
| 4 | Ver citas de médico por fecha | No ejecutado |
| 5 | Ver citas por fecha | No ejecutado |
| 6 | Ver citas programadas | No ejecutado |
| 7 | Ver citas confirmadas | No ejecutado |
| 8 | Ver citas canceladas | No ejecutado |
| 9 | Ver citas pendientes de hoy | No ejecutado |
| 10 | Ver próximas citas | No ejecutado |
| 11 | Consulta combinada | No ejecutado |
| 12 | Confirmar por ID | No ejecutado |
| 13 | Confirmar con datos naturales | No ejecutado |
| 14 | Confirmar cita ya confirmada | No ejecutado |
| 15 | Reprogramar por ID | No ejecutado |
| 16 | Reprogramar con datos naturales | No ejecutado |
| 17 | Verificar reprogramación | No ejecutado |
| 18 | Verificar horario anterior libre | No ejecutado |
| 19 | Verificar horario nuevo ocupado | No ejecutado |
| 20 | Reprogramar hacia horario ocupado | No ejecutado |
| 21 | Cancelar por ID | No ejecutado |
| 22 | Cancelar con datos naturales | No ejecutado |
| 23 | Verificar cita cancelada | No ejecutado |
| 24 | Verificar horario cancelado libre | No ejecutado |
| 25 | Cancelar cita ya cancelada | No ejecutado |
| 26 | Crear cita para completar | No ejecutado |
| 27 | Confirmar cita para completar | No ejecutado |
| 28 | Marcar como atendida | No ejecutado |
| 29 | Consultar citas completadas | No ejecutado |
| 30 | Cancelar cita completada | No ejecutado |
| 31 | Crear cita para inasistencia | No ejecutado |
| 32 | Marcar inasistencia | No ejecutado |
| 33 | Consultar inasistencias | No ejecutado |
| 34 | Cancelar sin datos suficientes | No ejecutado |
| 35 | Reprogramar sin fecha | No ejecutado |
| 36 | Reprogramar sin hora | No ejecutado |
| 37 | Confirmar sin identificar cita | No ejecutado |
| 38 | Agendar en fecha pasada | No ejecutado |
| 39 | Crear cita duplicada | No ejecutado |
| 40 | Duración inválida | No ejecutado |
| 41 | Médico inexistente | No ejecutado |
| 42 | Paciente inexistente | No ejecutado |
| 43 | Cancelación conversacional | No ejecutado |
| 44 | Reprogramación conversacional | No ejecutado |

## Criterio general de aprobación

La funcionalidad puede considerarse aprobada cuando:

- Las citas pueden consultarse por paciente, médico, fecha y estado.
- Las próximas citas aparecen ordenadas.
- Una cita puede cambiar de `scheduled` a `confirmed`.
- Una cita puede cambiar de `confirmed` a `completed`.
- Una cita puede marcarse como `no_show`.
- Una cita puede cancelarse sin eliminarse.
- La cancelación libera el horario.
- La reprogramación libera el horario anterior y ocupa el nuevo.
- El agente no elige registros arbitrariamente cuando hay ambigüedad.
- Las transiciones de estado inválidas son rechazadas.
- Los mensajes de error son entendibles para el usuario.
