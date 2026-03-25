from django.test import TestCase
from django.utils import timezone

from datetime import date, time, timedelta

from .forms import AppointmentForm
from .models import Appointment, SmsMessage
from .sms import (
    send_appointment_closed,
    send_appointment_closed_force,
    send_appointment_confirmation,
    send_appointment_confirmation_force,
)

# Create your tests here.


class AppointmentFormValidationTests(TestCase):
    def test_rejects_past_preferred_date(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        form = AppointmentForm(
            data={
                "full_name": "A",
                "phone": "1",
                "email": "a@example.com",
                "date_of_birth": "2000-01-01",
                "preferred_date": yesterday.isoformat(),
                "preferred_time": "10:00",
                "reason": "",
                "message": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("preferred_date", form.errors)

    def test_rejects_future_date_of_birth(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        form = AppointmentForm(
            data={
                "full_name": "A",
                "phone": "1",
                "email": "a@example.com",
                "date_of_birth": tomorrow.isoformat(),
                "preferred_date": timezone.localdate().isoformat(),
                "preferred_time": "10:00",
                "reason": "",
                "message": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)

    def test_enforces_buffer_time(self):
        d = timezone.localdate() + timedelta(days=1)
        Appointment.objects.create(
            full_name="Existing",
            phone="1",
            email="e@example.com",
            date_of_birth=date(2000, 1, 1),
            preferred_date=d,
            preferred_time=time(10, 0),
        )

        form = AppointmentForm(
            data={
                "full_name": "New",
                "phone": "2",
                "email": "n@example.com",
                "date_of_birth": "2001-01-01",
                "preferred_date": d.isoformat(),
                "preferred_time": "10:05",
                "reason": "",
                "message": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("preferred_time", form.errors)

    def test_allows_slot_outside_buffer(self):
        d = timezone.localdate() + timedelta(days=1)
        Appointment.objects.create(
            full_name="Existing",
            phone="1",
            email="e@example.com",
            date_of_birth=date(2000, 1, 1),
            preferred_date=d,
            preferred_time=time(10, 0),
        )

        form = AppointmentForm(
            data={
                "full_name": "New",
                "phone": "2",
                "email": "n@example.com",
                "date_of_birth": "2001-01-01",
                "preferred_date": d.isoformat(),
                "preferred_time": "10:10",
                "reason": "",
                "message": "",
            }
        )
        self.assertTrue(form.is_valid())


class AppointmentSmsTests(TestCase):
    def test_confirmation_sms_is_logged_and_timestamped(self):
        d = timezone.localdate() + timedelta(days=1)
        appt = Appointment.objects.create(
            full_name="Test",
            phone="999",
            email="t@example.com",
            date_of_birth=date(2000, 1, 1),
            preferred_date=d,
            preferred_time=time(10, 0),
        )

        sms = send_appointment_confirmation(appt)
        self.assertIsNotNone(sms)
        appt.refresh_from_db()
        self.assertIsNotNone(appt.confirmation_sms_sent_at)
        self.assertEqual(SmsMessage.objects.count(), 1)
        self.assertEqual(sms.kind, SmsMessage.Kind.APPOINTMENT_CONFIRMATION)
        self.assertEqual(sms.status, SmsMessage.Status.SENT)

    def test_closure_sms_is_logged_and_timestamped(self):
        d = timezone.localdate() + timedelta(days=1)
        appt = Appointment.objects.create(
            full_name="Test",
            phone="999",
            email="t@example.com",
            date_of_birth=date(2000, 1, 1),
            preferred_date=d,
            preferred_time=time(10, 0),
        )

        sms = send_appointment_closed(appt)
        self.assertIsNotNone(sms)
        appt.refresh_from_db()
        self.assertIsNotNone(appt.closure_sms_sent_at)
        self.assertEqual(SmsMessage.objects.count(), 1)
        self.assertEqual(sms.kind, SmsMessage.Kind.APPOINTMENT_CLOSED)
        self.assertEqual(sms.status, SmsMessage.Status.SENT)

    def test_force_confirmation_sends_again(self):
        d = timezone.localdate() + timedelta(days=1)
        appt = Appointment.objects.create(
            full_name="Test",
            phone="999",
            email="t@example.com",
            date_of_birth=date(2000, 1, 1),
            preferred_date=d,
            preferred_time=time(10, 0),
        )

        sms1 = send_appointment_confirmation(appt)
        self.assertIsNotNone(sms1)
        sms2 = send_appointment_confirmation_force(appt)
        self.assertIsNotNone(sms2)
        self.assertEqual(SmsMessage.objects.filter(kind=SmsMessage.Kind.APPOINTMENT_CONFIRMATION).count(), 2)

    def test_force_closure_sends_again(self):
        d = timezone.localdate() + timedelta(days=1)
        appt = Appointment.objects.create(
            full_name="Test",
            phone="999",
            email="t@example.com",
            date_of_birth=date(2000, 1, 1),
            preferred_date=d,
            preferred_time=time(10, 0),
        )

        sms1 = send_appointment_closed(appt)
        self.assertIsNotNone(sms1)
        sms2 = send_appointment_closed_force(appt)
        self.assertIsNotNone(sms2)
        self.assertEqual(SmsMessage.objects.filter(kind=SmsMessage.Kind.APPOINTMENT_CLOSED).count(), 2)
