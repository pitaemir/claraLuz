from django.db import migrations, models
import secrets


def _gen():
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "CL-" + "".join(secrets.choice(alphabet) for _ in range(8))


def populate_public_id(apps, schema_editor):
    LattesRequest = apps.get_model("siteapp", "LattesRequest")

    for r in LattesRequest.objects.all():
        if r.public_id:
            continue
        for _ in range(30):
            candidate = _gen()
            if not LattesRequest.objects.filter(public_id=candidate).exists():
                r.public_id = candidate
                r.save(update_fields=["public_id"])
                break


class Migration(migrations.Migration):

    dependencies = [
        ("siteapp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lattesrequest",
            name="public_id",
            field=models.CharField(blank=True, db_index=True, max_length=20, unique=True),
        ),
        migrations.RunPython(populate_public_id, migrations.RunPython.noop),
    ]
