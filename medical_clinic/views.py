from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import AppointmentForm
from .models import CaseStudy
from .sms import send_appointment_confirmation

def home(request):
    return render(request, 'medical_clinic/home.html')

def about_doctor(request):
    case_studies = CaseStudy.objects.filter(is_published=True)
    return render(request, 'medical_clinic/about_doctor.html', {"case_studies": case_studies})

def services(request):
    return render(request, 'medical_clinic/services.html')

def book_appointment(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            send_appointment_confirmation(appointment)
            messages.success(
                request,
                f"Appointment registered successfully. Your appointment ID is #{appointment.id}.",
            )
            return redirect("book_appointment")
    else:
        form = AppointmentForm()

    return render(request, "medical_clinic/book_appointment.html", {"form": form})
