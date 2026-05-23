from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from login.models import Role

User = get_user_model()

ROLE_TO_USERS = {
    "Admin": [
        {"email": "admin1@gmail.com", "password": "password123", "first": "Jeffrey", "last": "Kawabata", "superuser": True},
        {"email": "admin2@gmail.com", "password": "password123", "first": "Mitch", "last": "Twolentino", "superuser": True},
    ],
    "Staff": [
        {"email": "staff1@gmail.com", "password": "password123", "first": "Juan", "last": "Dela Cruz", "superuser": False},
        {"email": "staff2@gmail.com", "password": "password123", "first": "Harley", "last": "Queen", "superuser": False},
        {"email": "staff3@gmail.com", "password": "password123", "first": "Ce", "last": "Ce", "superuser": False},
    ],
}

DEFAULT_ROLE_MODULES = {
    "Admin": ["All"],
    "Staff": ["Home", "Documents", "Policies", "RecentNews", "Others"],
}

class Command(BaseCommand):
    help = "Create or update demo users (admins + staff)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing users before creating demo users.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]

        for role_name, modules in DEFAULT_ROLE_MODULES.items():
            Role.objects.update_or_create(
                role_name=role_name,
                defaults={"modules": ", ".join(modules)},
            )

        if reset:
            self.stdout.write(self.style.WARNING("Reset requested: deleting all users..."))
            User.objects.all().delete()

        def upsert(email, password, first, last, superuser, role_name):
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": first, "last_name": last},
            )

            user.email = email
            user.first_name = first
            user.last_name = last
            user.is_active = True
            user.is_superuser = bool(superuser)
            user.is_staff = bool(superuser)
            user.set_password(password)
            user.save()

            role = Role.objects.get(role_name=role_name)
            user.role = role
            user.save(update_fields=["role"])

            return created

        # Create users
        for role, users in ROLE_TO_USERS.items():
            for u in users:
                created = upsert(
                    u["email"], u["password"], u["first"], u["last"], u["superuser"], role
                )
                msg = f"{'Created' if created else 'Updated'} {role}: {u['email']}"
                self.stdout.write(self.style.SUCCESS(msg))

        self.stdout.write(self.style.SUCCESS("Done."))