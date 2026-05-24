from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User


class Command(BaseCommand):
    help = "Create a default admin account if it doesn't exist"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=getattr(settings, "DEFAULT_ADMIN_USERNAME", "admin"),
            help="Username for the admin account",
        )
        parser.add_argument(
            "--email",
            default=getattr(settings, "DEFAULT_ADMIN_EMAIL", "admin@example.com"),
            help="Email for the admin account",
        )
        parser.add_argument(
            "--password",
            default=getattr(settings, "DEFAULT_ADMIN_PASSWORD", "admin123"),
            help="Password for the admin account",
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Reset password if the admin account already exists",
        )

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        reset_password = options["reset_password"]

        user = User.objects.filter(username=username).first()
        if user is None and email:
            user = User.objects.filter(email=email).first()

        if user is None:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="admin",
                full_name="Admin System",
                is_verified=True,
                status="approved",
            )
           
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Created admin user: username='{username}', email='{email}'"
            ))
            return

     
        updated = False
        if reset_password and password:
            user.set_password(password)
            updated = True
  
        desired_changes = False
        if getattr(user, "role", None) != "admin":
            user.role = "admin"
            desired_changes = True
        if not user.is_staff:
            user.is_staff = True
            desired_changes = True
        if not user.is_superuser:
            user.is_superuser = True
            desired_changes = True
        if not getattr(user, "is_verified", True):
            user.is_verified = True
            desired_changes = True
        if getattr(user, "status", "approved") != "approved":
            user.status = "approved"
            desired_changes = True

        if updated or desired_changes:
            user.save()
            self.stdout.write(self.style.SUCCESS(
                "Updated existing admin user with requested changes"
            ))
        else:
            self.stdout.write("Admin user already exists and is up-to-date.")


