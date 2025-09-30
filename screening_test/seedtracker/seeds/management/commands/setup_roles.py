# seeds/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from seeds.permissions import STAFF_GROUP, AUDITOR_GROUP

class Command(BaseCommand):
    help = "Create Staff and Auditor groups and test users."

    def handle(self, *args, **kwargs):
        staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP)
        auditor_group, _ = Group.objects.get_or_create(name=AUDITOR_GROUP)

        if not User.objects.filter(username="staff").exists():
            u = User.objects.create_user(username="staff", password="staff123")
            u.groups.add(staff_group)
            self.stdout.write(self.style.SUCCESS("Created staff user: staff/staff123"))

        if not User.objects.filter(username="auditor").exists():
            u = User.objects.create_user(username="auditor", password="auditor123")
            u.groups.add(auditor_group)
            self.stdout.write(self.style.SUCCESS("Created auditor user: auditor/auditor123"))
