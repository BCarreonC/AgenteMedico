import unittest

from app.nodes.responder import (
    respond_cancelled_appointment,
    respond_list_appointments,
    respond_rescheduled_appointment,
)


APPOINTMENT = {
    "_id": "66a1d80e88b6a3af95cb9290",
    "doctorId": {
        "userId": {"fullName": "Ana López"},
    },
    "patientId": {
        "firstName": "Juan",
        "lastName": "Pérez",
    },
    "date": "2026-08-04T00:00:00.000Z",
    "startTime": "12:00",
    "endTime": "12:30",
    "status": "scheduled",
    "reason": "Control general",
}


class ResponderTests(unittest.TestCase):
    def test_formats_appointment_list(self) -> None:
        response = respond_list_appointments(
            {
                "ok": True,
                "appointments": [APPOINTMENT],
            }
        )

        self.assertIn("Encontré 1 cita", response)
        self.assertIn("Juan Pérez", response)
        self.assertIn("Ana López", response)
        self.assertIn("2026-08-04", response)

    def test_formats_cancelled_appointment(self) -> None:
        cancelled = {
            **APPOINTMENT,
            "status": "cancelled",
            "cancellationReason": "No podrá asistir",
        }
        response = respond_cancelled_appointment(
            {
                "ok": True,
                "appointment": cancelled,
            }
        )

        self.assertIn("horario quedó liberado", response)
        self.assertIn("No podrá asistir", response)

    def test_formats_rescheduled_appointment(self) -> None:
        previous = {
            **APPOINTMENT,
            "date": "2026-08-03T00:00:00.000Z",
            "startTime": "10:30",
            "endTime": "11:00",
        }
        response = respond_rescheduled_appointment(
            {
                "ok": True,
                "previous_appointment": previous,
                "appointment": APPOINTMENT,
            }
        )

        self.assertIn("Horario anterior", response)
        self.assertIn("10:30", response)
        self.assertIn("Nuevo horario", response)
        self.assertIn("12:00", response)


if __name__ == "__main__":
    unittest.main()
