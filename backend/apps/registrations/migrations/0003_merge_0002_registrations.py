# Merge the independent client-registration and driver residential-area migrations.
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("registrations", "0002_clientregistration"),
        ("registrations", "0002_driverregistration_residential_area"),
    ]

    operations = []
