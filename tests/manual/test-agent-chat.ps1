param(
    [string]$AgentUrl = "http://localhost:8000/chat",
    [string]$PatientName = "Juan Pérez García",
    [string]$DoctorName = "Ana López",
    [string]$Date = "2026-07-30",
    [string]$CancelAppointmentId = "",
    [string]$RescheduleAppointmentId = "",
    [string]$ConfirmAppointmentId = "",
    [string]$CompleteAppointmentId = "",
    [string]$NoShowAppointmentId = "",
    [string]$NewDate = "2026-08-04",
    [string]$NewTime = "12:00"
)

$ErrorActionPreference = "Stop"

function Send-Chat {
    param(
        [string]$Message,
        [string]$SessionId
    )

    Write-Host "`nUSUARIO: $Message" -ForegroundColor Cyan

    $response = Invoke-RestMethod `
        -Method POST `
        -Uri $AgentUrl `
        -ContentType "application/json" `
        -Body (@{
            message = $Message
            session_id = $SessionId
        } | ConvertTo-Json)

    Write-Host "INTENT: $($response.intent)" -ForegroundColor Yellow
    Write-Host "RESPUESTA:`n$($response.response)" -ForegroundColor Green

    if (@($response.errors).Count -gt 0) {
        Write-Warning ($response.errors -join " | ")
    }

    return $response
}

Send-Chat `
    -SessionId "test-list-patient" `
    -Message "Muéstrame las citas de $PatientName"

Send-Chat `
    -SessionId "test-list-doctor" `
    -Message "¿Qué citas tiene la doctora $DoctorName el $Date?"

Send-Chat `
    -SessionId "test-list-pending" `
    -Message "¿Cuáles son las citas pendientes del $Date?"

if ($CancelAppointmentId) {
    Send-Chat `
        -SessionId "test-cancel" `
        -Message (
            "Cancela la cita con ID $CancelAppointmentId porque " +
            "el paciente no podrá asistir"
        )
}

if ($RescheduleAppointmentId) {
    Send-Chat `
        -SessionId "test-reschedule" `
        -Message (
            "Reprograma la cita con ID $RescheduleAppointmentId " +
            "para el $NewDate a las $NewTime por 30 minutos"
        )
}

if ($ConfirmAppointmentId) {
    Send-Chat `
        -SessionId "test-confirm" `
        -Message "Confirma la cita con ID $ConfirmAppointmentId"
}

if ($CompleteAppointmentId) {
    Send-Chat `
        -SessionId "test-complete" `
        -Message (
            "Marca como atendida la cita con ID $CompleteAppointmentId"
        )
}

if ($NoShowAppointmentId) {
    Send-Chat `
        -SessionId "test-no-show" `
        -Message (
            "El paciente no se presentó a la cita con ID " +
            "$NoShowAppointmentId"
        )
}
