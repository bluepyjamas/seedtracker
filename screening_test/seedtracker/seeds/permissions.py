
from django.contrib.auth.models import Group

STAFF_GROUP = "Staff"
AUDITOR_GROUP = "Auditor"

def user_is_staff_role(user):
    return user.is_authenticated and user.groups.filter(name=STAFF_GROUP).exists()

def user_is_auditor(user):
    return user.is_authenticated and user.groups.filter(name=AUDITOR_GROUP).exists()
