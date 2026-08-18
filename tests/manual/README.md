# Pruebas del agente por chat

## Requisitos

1. NestJS iniciado en el puerto 3000.
2. Ollama iniciado y con el modelo configurado en `.env`.
3. FastAPI iniciado en el puerto 8000.
4. Tener citas diferentes para cancelar, reprogramar, confirmar, completar y marcar como no presentado.

## Consultas sin modificar datos

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\manual\test-agent-chat.ps1 `
  -PatientName "Juan Pérez García" `
  -DoctorName "Ana López" `
  -Date "2026-07-30"
```

## Flujo completo

Pasa IDs distintos para cada transición:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\manual\test-agent-chat.ps1 `
  -PatientName "Juan Pérez García" `
  -DoctorName "Ana López" `
  -Date "2026-07-30" `
  -CancelAppointmentId "ID_CITA_CANCELAR" `
  -RescheduleAppointmentId "ID_CITA_REPROGRAMAR" `
  -ConfirmAppointmentId "ID_CITA_CONFIRMAR" `
  -CompleteAppointmentId "ID_CITA_COMPLETAR" `
  -NoShowAppointmentId "ID_CITA_NO_SHOW" `
  -NewDate "2026-08-04" `
  -NewTime "12:00"
```

## Pruebas unitarias de la herramienta

```powershell
python -m unittest discover -s tests -v
```
