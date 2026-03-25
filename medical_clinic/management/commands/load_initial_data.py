from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Load initial fixture data (specialists, etc.) for a fresh install."

    def handle(self, *args, **options):
        call_command("loaddata", "initial_data.json")
        self.stdout.write(self.style.SUCCESS("Initial data loaded."))
