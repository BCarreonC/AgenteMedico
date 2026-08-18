import unittest
from unittest.mock import AsyncMock, patch

from app.tools.appointments import AppointmentsTool


DOCTOR = {
    "_id": "66a1d70e88b6a3af95cb9261",
    "userId": {"fullName": "Ana López"},
    "specialty": "Medicina general",
}
PATIENT = {
    "_id": "66a1d75d88b6a3af95cb9278",
    "firstName": "Juan",
    "lastName": "Pérez",
}
APPOINTMENT = {
    "_id": "66a1d80e88b6a3af95cb9290",
    "doctorId": DOCTOR,
    "patientId": PATIENT,
    "date": "2026-08-04T00:00:00.000Z",
    "startTime": "12:00",
    "endTime": "12:30",
    "status": "scheduled",
    "reason": "Control general",
}


class AppointmentsToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tool = AppointmentsTool()

    async def test_list_appointments_resolves_patient(self) -> None:
        with (
            patch(
                "app.tools.appointments.api.search_patients",
                new=AsyncMock(return_value=[PATIENT]),
            ),
            patch(
                "app.tools.appointments.api.list_appointments",
                new=AsyncMock(return_value=[APPOINTMENT]),
            ) as list_mock,
        ):
            result = await self.tool.execute(
                {
                    "action": "list_appointments",
                    "patient_name": "Juan Pérez",
                    "upcoming": True,
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        list_mock.assert_awaited_once_with(
            patient_id=PATIENT["_id"],
            doctor_id=None,
            date=None,
            status=None,
            pending=None,
            upcoming=True,
        )

    async def test_cancel_returns_ambiguity_when_multiple_appointments_match(self) -> None:
        second = {**APPOINTMENT, "_id": "66a1d80e88b6a3af95cb9291"}

        with (
            patch(
                "app.tools.appointments.api.search_patients",
                new=AsyncMock(return_value=[PATIENT]),
            ),
            patch(
                "app.tools.appointments.api.list_appointments",
                new=AsyncMock(return_value=[APPOINTMENT, second]),
            ),
        ):
            result = await self.tool.execute(
                {
                    "action": "cancel_appointment",
                    "patient_name": "Juan Pérez",
                }
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "ambiguous_appointment")
        self.assertEqual(len(result["appointments"]), 2)

    async def test_reschedule_by_id_calls_api(self) -> None:
        updated = {
            **APPOINTMENT,
            "date": "2026-08-05T00:00:00.000Z",
            "startTime": "13:00",
            "endTime": "13:30",
        }

        with (
            patch(
                "app.tools.appointments.api.get_appointment",
                new=AsyncMock(return_value=APPOINTMENT),
            ),
            patch(
                "app.tools.appointments.api.reschedule_appointment",
                new=AsyncMock(return_value=updated),
            ) as reschedule_mock,
        ):
            result = await self.tool.execute(
                {
                    "action": "reschedule_appointment",
                    "appointment_id": APPOINTMENT["_id"],
                    "new_date": "2026-08-05",
                    "new_start_time": "13:00",
                    "duration_minutes": 30,
                }
            )

        self.assertTrue(result["ok"])
        reschedule_mock.assert_awaited_once_with(
            APPOINTMENT["_id"],
            date="2026-08-05",
            start_time="13:00",
            duration_minutes=30,
        )

    async def test_confirm_by_id_calls_api(self) -> None:
        confirmed = {**APPOINTMENT, "status": "confirmed"}

        with (
            patch(
                "app.tools.appointments.api.get_appointment",
                new=AsyncMock(return_value=APPOINTMENT),
            ),
            patch(
                "app.tools.appointments.api.confirm_appointment",
                new=AsyncMock(return_value=confirmed),
            ) as confirm_mock,
        ):
            result = await self.tool.execute(
                {
                    "action": "confirm_appointment",
                    "appointment_id": APPOINTMENT["_id"],
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["appointment"]["status"], "confirmed")
        confirm_mock.assert_awaited_once_with(APPOINTMENT["_id"])


if __name__ == "__main__":
    unittest.main()
