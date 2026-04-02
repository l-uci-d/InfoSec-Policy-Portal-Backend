from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

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

        # Ensure groups exist
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        staff_group, _ = Group.objects.get_or_create(name="Staff")

        if reset:
            self.stdout.write(self.style.WARNING("Reset requested: deleting all users..."))
            User.objects.all().delete()

        def upsert(email, password, first, last, superuser, group):
            # Keep username=email so authenticate(username=email, ...) works
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": first, "last_name": last},
            )

            user.email = email
            user.first_name = first
            user.last_name = last
            user.is_active = True
            user.is_superuser = bool(superuser)
            user.is_staff = bool(superuser)  # staff allows /admin access if you use it
            user.set_password(password)
            user.save()

            user.groups.clear()
            user.groups.add(group)

            return created

        # Create users
        for role, users in ROLE_TO_USERS.items():
            group = admin_group if role == "Admin" else staff_group
            for u in users:
                created = upsert(
                    u["email"], u["password"], u["first"], u["last"], u["superuser"], group
                )
                msg = f"{'Created' if created else 'Updated'} {role}: {u['email']}"
                self.stdout.write(self.style.SUCCESS(msg))

        self.stdout.write(self.style.SUCCESS("Done."))