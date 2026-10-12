import json
import os
from pathlib import Path
import subprocess

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import DetectionArtifact, DetectionCandidate, DetectionJob
from .reporting import ensure_pdf_report


@shared_task(bind=True, name="detection.run_detection_job")
def run_detection_job(self, job_id: int) -> None:
    job = DetectionJob.objects.get(pk=job_id)
    job.status = DetectionJob.Status.RUNNING
    job.progress = 5
    job.started_at = timezone.now()
    job.save(update_fields=("status", "progress", "started_at"))

    workspace = Path(settings.DETECTION_WORKSPACE_ROOT) / str(job.pk)
    workspace.mkdir(parents=True, exist_ok=True)
    manifest = workspace / "job.json"
    result_file = workspace / "result.json"
    manifest.write_text(
        json.dumps(
            {
                "job_id": job.pk,
                "aoi": job.aoi,
                "start_date": job.start_date.isoformat(),
                "end_date": job.end_date.isoformat(),
                "collection": job.collection,
                "workspace": str(workspace),
                "result_file": str(result_file),
            }
        ),
        encoding="utf-8",
    )
    job.output_directory = str(workspace)
    job.progress = 10
    job.save(update_fields=("output_directory", "progress"))

    command = [
        str(settings.ML_PYTHON),
        str(settings.ML_RUNNER),
        "--manifest",
        str(manifest),
    ]
    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    ml_pythonpath = str(settings.ML_ROOT)
    if environment.get("PYTHONPATH"):
        ml_pythonpath = os.pathsep.join(
            (ml_pythonpath, environment["PYTHONPATH"])
        )
    environment["PYTHONPATH"] = ml_pythonpath
    try:
        completed = subprocess.run(
            command,
            cwd=str(settings.ML_ROOT),
            env=environment,
            capture_output=True,
            text=True,
            timeout=settings.DETECTION_JOB_TIMEOUT_SECONDS,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or completed.stdout.strip()
                or "ML worker exited with a non-zero status."
            )
        result = json.loads(result_file.read_text(encoding="utf-8"))
        _persist_result(job, result)
    except Exception as exc:
        job.status = DetectionJob.Status.FAILED
        job.error_message = str(exc)[:4000]
        job.completed_at = timezone.now()
        job.save(update_fields=("status", "error_message", "completed_at"))
        raise


def _persist_result(job: DetectionJob, result: dict) -> None:
    job.scene_metadata = result.get("scene_metadata", {})
    job.result_summary = result.get("pipeline", {})
    job.progress = 100
    job.status = DetectionJob.Status.SUCCEEDED
    job.completed_at = timezone.now()
    job.save(
        update_fields=(
            "scene_metadata",
            "result_summary",
            "progress",
            "status",
            "completed_at",
        )
    )

    for candidate in result.get("candidates", []):
        DetectionCandidate.objects.update_or_create(
            job=job,
            candidate_id=candidate["candidate_id"],
            defaults={
                "status": candidate.get("status", "REQUIRES_VERIFICATION"),
                "geometry": candidate["geometry"],
                "attributes": candidate.get("attributes", {}),
            },
        )
    for artifact in result.get("artifacts", []):
        DetectionArtifact.objects.create(
            job=job,
            kind=artifact["kind"],
            name=artifact["name"],
            path=artifact["path"],
        )
    ensure_pdf_report(job)
