from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tapp", "0002_auto_20170611_2026"),
    ]

    operations = [
        migrations.CreateModel(
            name="BigItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
            ],
            options={
                "db_table": "big_item",
                "abstract": False,
            },
        ),
    ]
