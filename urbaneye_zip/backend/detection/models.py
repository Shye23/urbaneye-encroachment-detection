from django.conf import settings
from django.db import models


class DetectionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="detection_jobs",
    )
    aoi = models.JSONField()
    start_date = models.DateField()
    end_date = models.DateField()
    collection = models.CharField(
        max_length=200,
        default="ResourceSat-2_LISS4-MX70_L2",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    progress = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True)
    scene_metadata = models.JSONField(default=dict, blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    output_directory = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class DetectionCandidate(models.Model):
    job = models.ForeignKey(
        DetectionJob,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    candidate_id = models.CharField(max_length=50)
    status = models.CharField(
        max_length=30,
        default="REQUIRES_VERIFICATION",
    )
    geometry = models.JSONField()
    attributes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("job", "candidate_id"),
                name="unique_detection_candidate_per_job",
            ),
        ]


class DetectionArtifact(models.Model):
    class Kind(models.TextChoices):
        GEOJSON = "GEOJSON", "GeoJSON"
        REPORT = "REPORT", "Report"
        EVIDENCE = "EVIDENCE", "Evidence"
        RASTER = "RASTER", "Raster"

    job = models.ForeignKey(
        DetectionJob,
        on_delete=models.CASCADE,
        related_name="artifacts",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
