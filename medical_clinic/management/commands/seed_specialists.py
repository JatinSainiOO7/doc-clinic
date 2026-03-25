from django.core.management.base import BaseCommand

from medical_clinic.models import Specialist


class Command(BaseCommand):
    help = "Create a few sample specialists if they don't exist."

    def handle(self, *args, **options):
        samples = [
            {
                "name": "Dr. Sonam Rivers",
                "specialty": "Neurologist",
                "experience": "12+ years",
                "description": "Brain and nerve care, migraine management, and neurological evaluations.",
                "sort_order": 10,
            },
            {
                "name": "Dr. Priya Mehta",
                "specialty": "Pediatrics",
                "experience": "Child care",
                "description": "Infant and child check-ups, vaccinations, and family guidance.",
                "sort_order": 20,
            },
            {
                "name": "Dr. Michael Chen",
                "specialty": "General Medicine",
                "experience": "Primary care",
                "description": "Routine check-ups, follow-ups, and coordinated specialist referrals.",
                "sort_order": 30,
            },
        ]

        created = 0
        updated = 0
        for s in samples:
            obj, was_created = Specialist.objects.get_or_create(
                name=s["name"],
                defaults={
                    "specialty": s["specialty"],
                    "experience": s["experience"],
                    "description": s["description"],
                    "image_url": "/static/images/doctor.jpg",
                    "is_published": True,
                    "sort_order": s["sort_order"],
                },
            )
            if was_created:
                created += 1
                continue

            changed = False
            for field in ["specialty", "experience", "description", "sort_order"]:
                if getattr(obj, field) != s[field]:
                    setattr(obj, field, s[field])
                    changed = True
            if not obj.image_url:
                obj.image_url = "/static/images/doctor.jpg"
                changed = True
            if not obj.is_published:
                obj.is_published = True
                changed = True
            if changed:
                obj.save(
                    update_fields=[
                        "specialty",
                        "experience",
                        "description",
                        "image_url",
                        "is_published",
                        "sort_order",
                        "updated_at",
                    ]
                )
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Specialists seeded. Created: {created}, Updated: {updated}"))
