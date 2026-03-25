from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.utils import timezone
from .models import Appointment, CaseStudy, SmsMessage, Specialist, ClinicSettings
from .sms import (
    send_appointment_closed,
    send_appointment_closed_force,
    send_appointment_confirmation,
    send_appointment_confirmation_force,
)


admin.site.site_header = "DoClinic Admin"
admin.site.site_title = "DoClinic Admin"
admin.site.index_title = "Clinic Management"


@admin.register(SmsMessage)
class SmsMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "kind",
        "status",
        "provider",
        "to_phone",
        "appointment",
        "created_at",
        "sent_at",
    )
    list_filter = ("kind", "status", "provider", "created_at")
    search_fields = ("to_phone", "body", "appointment__full_name", "appointment__id")
    ordering = ("-created_at",)
    list_per_page = 50

    readonly_fields = (
        "to_phone",
        "body",
        "kind",
        "status",
        "provider",
        "error",
        "appointment",
        "created_at",
        "sent_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")
    readonly_fields = ("updated_at", "open_in_maps_url", "embed_url")
    fields = (
        "address",
        "hours",
        "maps_query",
        "maps_open_url",
        "maps_embed_url",
        "open_in_maps_url",
        "embed_url",
        "updated_at",
    )

    def has_add_permission(self, request):
        return ClinicSettings.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        return False


class AppointmentDayFilter(admin.SimpleListFilter):
    title = "day"
    parameter_name = "day"

    def lookups(self, request, model_admin):
        return [
            ("today", "Today"),
            ("tomorrow", "Tomorrow"),
            ("next_7", "Next 7 days"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        today = timezone.localdate()
        if value == "today":
            return queryset.filter(preferred_date=today)
        if value == "tomorrow":
            return queryset.filter(preferred_date=today + timezone.timedelta(days=1))
        if value == "next_7":
            return queryset.filter(
                preferred_date__gte=today,
                preferred_date__lte=today + timezone.timedelta(days=7),
            )
        return queryset


class AppointmentStatusFilter(admin.SimpleListFilter):
    title = "status"
    parameter_name = "status_tab"

    def lookups(self, request, model_admin):
        return [
            (Appointment.Status.OPEN, "Open"),
            (Appointment.Status.COMPLETED, "Completed"),
            (Appointment.Status.NO_SHOW, "No-show"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        return queryset.filter(status=value)


class SmsMessageInline(admin.TabularInline):
    model = SmsMessage
    extra = 0
    can_delete = False
    fields = ("created_at", "kind", "status", "provider", "to_phone", "sent_at")
    readonly_fields = fields
    ordering = ("-created_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    date_hierarchy = "preferred_date"
    list_display = (
        "id",
        "full_name",
        "phone",
        "email",
        "date_of_birth",
        "preferred_date",
        "preferred_time",
        "status_badge",
        "closed_at",
        "created_at",
    )
    list_filter = (AppointmentStatusFilter, AppointmentDayFilter, "preferred_date", "created_at")
    search_fields = ("full_name", "phone", "email", "reason", "message")
    readonly_fields = ("created_at", "closed_at", "confirmation_sms_sent_at", "closure_sms_sent_at")
    ordering = ("preferred_date", "preferred_time", "-created_at")
    list_per_page = 50
    inlines = [SmsMessageInline]

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.status == Appointment.Status.COMPLETED:
            return format_html(
                '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;background:#dcfce7;color:#166534;font-weight:700;">{}</span>',
                "Completed",
            )
        if obj.status == Appointment.Status.NO_SHOW:
            return format_html(
                '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;background:#fee2e2;color:#991b1b;font-weight:700;">{}</span>',
                "No-show",
            )
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;background:#dbeafe;color:#1e40af;font-weight:700;">{}</span>',
            "Open",
        )

    actions = [
        "resend_confirmation_sms",
        "send_closing_sms_now",
        "mark_completed_and_notify",
        "mark_no_show",
    ]

    @admin.action(description="Resend confirmation SMS")
    def resend_confirmation_sms(self, request, queryset):
        sent = 0
        skipped = 0
        for appt in queryset:
            sms = send_appointment_confirmation_force(appt)
            if sms is None:
                skipped += 1
                continue
            if sms.status == SmsMessage.Status.SENT:
                sent += 1
        self.message_user(request, f"Sent {sent} confirmation SMS. Skipped {skipped}.")

    @admin.action(description="Send closing SMS now")
    def send_closing_sms_now(self, request, queryset):
        sent = 0
        skipped = 0
        for appt in queryset:
            if appt.status != Appointment.Status.COMPLETED:
                skipped += 1
                continue
            sms = send_appointment_closed_force(appt)
            if sms is None:
                skipped += 1
                continue
            if sms.status == SmsMessage.Status.SENT:
                sent += 1
        self.message_user(request, f"Sent {sent} closing SMS. Skipped {skipped}.")

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = Appointment.objects.filter(pk=obj.pk).values_list("status", flat=True).first()

        if obj.status in {Appointment.Status.COMPLETED, Appointment.Status.NO_SHOW} and not obj.closed_at:
            obj.closed_at = timezone.now()

        super().save_model(request, obj, form, change)

        if previous_status and previous_status != obj.status and obj.status == Appointment.Status.COMPLETED:
            send_appointment_closed(obj)

    @admin.action(description="Mark completed and send closing SMS")
    def mark_completed_and_notify(self, request, queryset):
        now = timezone.now()
        updated = 0
        for appt in queryset:
            if appt.status != Appointment.Status.COMPLETED:
                appt.status = Appointment.Status.COMPLETED
                appt.closed_at = appt.closed_at or now
                appt.save(update_fields=["status", "closed_at"])
                send_appointment_closed(appt)
                updated += 1
        self.message_user(request, f"Updated {updated} appointment(s).")

    @admin.action(description="Mark as no-show")
    def mark_no_show(self, request, queryset):
        now = timezone.now()
        updated = 0
        for appt in queryset:
            if appt.status != Appointment.Status.NO_SHOW:
                appt.status = Appointment.Status.NO_SHOW
                appt.closed_at = appt.closed_at or now
                appt.save(update_fields=["status", "closed_at"])
                updated += 1
        self.message_user(request, f"Updated {updated} appointment(s).")


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.DateField: {"widget": forms.DateInput(attrs={"type": "date"})},
    }
    date_hierarchy = "occurred_on"
    list_display = (
        "id",
        "image_preview",
        "title",
        "tag",
        "occurred_on",
        "is_published",
        "sort_order",
        "updated_at",
    )
    list_filter = ("is_published", "tag")
    search_fields = ("title", "tag", "summary")
    list_editable = ("sort_order", "is_published")
    ordering = ("sort_order", "-occurred_on", "-created_at")

    readonly_fields = ("image_preview",)
    fields = (
        "title",
        "tag",
        "occurred_on",
        "image",
        "image_url",
        "image_preview",
        "summary",
        "is_published",
        "sort_order",
    )

    @admin.display(description="Image")
    def image_preview(self, obj):
        src = None
        if getattr(obj, "image", None):
            try:
                src = obj.image.url
            except ValueError:
                src = None
        if not src and getattr(obj, "image_url", None):
            src = obj.image_url
        if not src:
            return "-"
        return format_html(
            '<img src="{}" style="height:48px;width:80px;object-fit:contain;background:#0f172a;border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:4px;" />',
            src,
        )


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "image_preview",
        "name",
        "specialty",
        "experience",
        "is_published",
        "sort_order",
        "updated_at",
    )
    list_filter = ("is_published", "specialty")
    search_fields = ("name", "specialty", "description")
    list_editable = ("sort_order", "is_published")
    ordering = ("sort_order", "name")

    readonly_fields = ("image_preview",)
    fields = (
        "name",
        "specialty",
        "experience",
        "image",
        "image_url",
        "image_preview",
        "description",
        "is_published",
        "sort_order",
    )

    @admin.display(description="Image")
    def image_preview(self, obj):
        src = None
        if getattr(obj, "image", None):
            try:
                src = obj.image.url
            except ValueError:
                src = None
        if not src and getattr(obj, "image_url", None):
            src = obj.image_url
        if not src:
            return "-"
        return format_html(
            '<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:9999px;border:1px solid rgba(255,255,255,.12);background:#0f172a;" />',
            src,
        )
