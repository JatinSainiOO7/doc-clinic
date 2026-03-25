from django.db import models
from django.utils import timezone

class Appointment(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        COMPLETED = "completed", "Completed"
        NO_SHOW = "no_show", "No-show"

    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    closed_at = models.DateTimeField(blank=True, null=True)
    confirmation_sms_sent_at = models.DateTimeField(blank=True, null=True)
    closure_sms_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.preferred_date})"


class SmsMessage(models.Model):
    class Kind(models.TextChoices):
        APPOINTMENT_CONFIRMATION = "appointment_confirmation", "Appointment confirmation"
        APPOINTMENT_CLOSED = "appointment_closed", "Appointment closed"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    to_phone = models.CharField(max_length=30)
    body = models.TextField()
    kind = models.CharField(max_length=40, choices=Kind.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    provider = models.CharField(max_length=40, blank=True)
    error = models.TextField(blank=True)
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_messages",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind} to {self.to_phone} ({self.status})"


class CaseStudy(models.Model):
    title = models.CharField(max_length=160)
    tag = models.CharField(max_length=80, blank=True)
    occurred_on = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to="case_studies/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-occurred_on", "-created_at"]

    def __str__(self):
        return self.title


class Specialist(models.Model):
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=120, blank=True)
    experience = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="specialists/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name", "-created_at"]

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    quote = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    avatar_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name
