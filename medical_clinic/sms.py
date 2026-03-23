from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from .models import Appointment, SmsMessage


@dataclass(frozen=True)
class SmsSendResult:
    status: str
    provider: str
    error: str = ""


def _normalize_phone(phone: str) -> str:
    return (phone or "").strip()


def send_sms(*, to_phone: str, body: str, kind: str, appointment: Appointment | None = None) -> SmsMessage:
    to_phone = _normalize_phone(to_phone)
    message = SmsMessage.objects.create(
        to_phone=to_phone,
        body=body,
        kind=kind,
        appointment=appointment,
    )

    backend = getattr(settings, "SMS_BACKEND", "console")
    if backend == "console":
        message.status = SmsMessage.Status.SENT
        message.provider = "console"
        message.sent_at = timezone.now()
        message.save(update_fields=["status", "provider", "sent_at"])
        return message

    message.status = SmsMessage.Status.FAILED
    message.provider = backend
    message.error = f"Unsupported SMS_BACKEND: {backend}"
    message.save(update_fields=["status", "provider", "error"])
    return message


def send_appointment_confirmation(appointment: Appointment) -> SmsMessage | None:
    if appointment.confirmation_sms_sent_at:
        return None
    if not appointment.phone:
        return None

    time_part = appointment.preferred_time.strftime("%H:%M") if appointment.preferred_time else ""
    when = f"{appointment.preferred_date.isoformat()} {time_part}".strip()
    body = (
        f"DoClinic: Appointment #{appointment.id} booked. "
        f"Name: {appointment.full_name}. Preferred: {when}."
    )
    sms = send_sms(
        to_phone=appointment.phone,
        body=body,
        kind=SmsMessage.Kind.APPOINTMENT_CONFIRMATION,
        appointment=appointment,
    )
    if sms.status == SmsMessage.Status.SENT:
        appointment.confirmation_sms_sent_at = timezone.now()
        appointment.save(update_fields=["confirmation_sms_sent_at"])
    return sms


def send_appointment_closed(appointment: Appointment) -> SmsMessage | None:
    if appointment.closure_sms_sent_at:
        return None
    if not appointment.phone:
        return None

    body = f"DoClinic: Appointment #{appointment.id} is closed. Thank you for visiting."
    sms = send_sms(
        to_phone=appointment.phone,
        body=body,
        kind=SmsMessage.Kind.APPOINTMENT_CLOSED,
        appointment=appointment,
    )
    if sms.status == SmsMessage.Status.SENT:
        appointment.closure_sms_sent_at = timezone.now()
        appointment.save(update_fields=["closure_sms_sent_at"])
    return sms

