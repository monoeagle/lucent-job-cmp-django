"""Management command to seed stub users."""
from django.core.management.base import BaseCommand
from apps.accounts.services import AccountService


class Command(BaseCommand):
    help = "Create stub users for development"

    def handle(self, *args, **options):
        created = AccountService.seed_stub_users()
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} stub user(s)."))
