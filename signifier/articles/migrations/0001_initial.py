
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Article",
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
                ("length", models.FloatField(blank=True, null=True)),
                ("has_audio", models.BooleanField(default=False)),
                ("stale_audio", models.BooleanField(default=False)),
                ("datetime", models.DateTimeField()),
                ("original_title", models.CharField(max_length=128, unique=True)),
                ("title", models.CharField(max_length=128, unique=True)),
                ("filename", models.CharField(max_length=180, unique=True)),
                ("url", models.URLField(unique=True)),
                ("rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("position", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("downloaded", models.BooleanField(default=False)),
                (
                    "edited_filename",
                    models.CharField(blank=True, max_length=180, null=True),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Series",
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
                ("name", models.CharField(max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Source",
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
                ("site", models.CharField(max_length=32)),
                ("author", models.CharField(blank=True, default="", max_length=32)),
                ("name", models.CharField(blank=True, default="", max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name="Tag",
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
                ("name", models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Highlights",
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
                ("length", models.FloatField(blank=True, null=True)),
                ("has_audio", models.BooleanField(default=False)),
                ("stale_audio", models.BooleanField(default=False)),
                ("datetime", models.DateTimeField()),
                ("number", models.PositiveSmallIntegerField()),
                (
                    "article",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="highlights",
                        to="articles.article",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="article",
            name="series",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="articles.series",
            ),
        ),
        migrations.AddField(
            model_name="article",
            name="source",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="articles.source"
            ),
        ),
    ]
