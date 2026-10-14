from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("registrations", "0001_initial")]
    operations = [migrations.AddField(model_name="driverregistration", name="residential_area", field=models.CharField(blank=True, max_length=120))]
