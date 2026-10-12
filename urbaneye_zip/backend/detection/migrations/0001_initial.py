from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DetectionJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("aoi", models.JSONField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("collection", models.CharField(default="ResourceSat-2_LISS4-MX70_L2", max_length=200)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("RUNNING", "Running"), ("SUCCEEDED", "Succeeded"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("scene_metadata", models.JSONField(blank=True, default=dict)),
                ("result_summary", models.JSONField(blank=True, default=dict)),
                ("output_directory", models.CharField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="detection_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DetectionArtifact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("GEOJSON", "GeoJSON"), ("REPORT", "Report"), ("EVIDENCE", "Evidence"), ("RASTER", "Raster")], max_length=20)),
                ("name", models.CharField(max_length=255)),
                ("path", models.CharField(max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="artifacts", to="detection.detectionjob")),
            ],
        ),
        migrations.CreateModel(
            name="DetectionCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("candidate_id", models.CharField(max_length=50)),
                ("status", models.CharField(default="REQUIRES_VERIFICATION", max_length=30)),
                ("geometry", models.JSONField()),
                ("attributes", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidates", to="detection.detectionjob")),
            ],
        ),
        migrations.AddConstraint(
            model_name="detectioncandidate",
            constraint=models.UniqueConstraint(fields=("job", "candidate_id"), name="unique_detection_candidate_per_job"),
        ),
    ]
