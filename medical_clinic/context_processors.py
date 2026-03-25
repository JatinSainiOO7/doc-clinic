from .models import ClinicSettings


def clinic(request):
    return {"clinic": ClinicSettings.get_solo()}
