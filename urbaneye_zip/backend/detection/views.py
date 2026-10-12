from pathlib import Path

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminOrDepartmentOfficer

from .models import DetectionJob
from .models import DetectionArtifact
from .serializers import DetectionJobCreateSerializer, DetectionJobSerializer
from .tasks import run_detection_job
from .reporting import ensure_pdf_report


class DetectionJobListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrDepartmentOfficer]

    def get_queryset(self):
        return DetectionJob.objects.filter(
            requested_by=self.request.user
        ).prefetch_related("candidates", "artifacts")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DetectionJobCreateSerializer
        return DetectionJobSerializer

    def perform_create(self, serializer):
        job = serializer.save(requested_by=self.request.user)
        run_detection_job.delay(job.pk)
        self.created_job = job

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = DetectionJobSerializer(
            self.created_job,
            context={"request": request},
        ).data
        return Response(response.data, status=status.HTTP_202_ACCEPTED)


class DetectionJobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrDepartmentOfficer]
    serializer_class = DetectionJobSerializer

    def get_queryset(self):
        return DetectionJob.objects.filter(
            requested_by=self.request.user
        ).prefetch_related("candidates", "artifacts")


class DetectionReportListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrDepartmentOfficer]
    serializer_class = DetectionJobSerializer

    def get_queryset(self):
        jobs = DetectionJob.objects.filter(
            requested_by=self.request.user
        ).prefetch_related("candidates", "artifacts")
        for job in jobs:
            if job.status == DetectionJob.Status.SUCCEEDED:
                ensure_pdf_report(job)
                job._prefetched_objects_cache.pop("artifacts", None)
        return jobs


class DetectionArtifactDownloadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrDepartmentOfficer]

    def get(self, request, job_id, artifact_id):
        job = get_object_or_404(
            DetectionJob,
            pk=job_id,
            requested_by=request.user,
        )
        artifact = get_object_or_404(
            DetectionArtifact,
            pk=artifact_id,
            job=job,
            kind=DetectionArtifact.Kind.REPORT,
        )
        if not artifact.name.lower().endswith(".pdf"):
            return Response(
                {"detail": "Only PDF reports can be downloaded here."},
                status=status.HTTP_404_NOT_FOUND,
            )
        artifact_path = Path(artifact.path).resolve()
        workspace = Path(job.output_directory).resolve()
        if workspace not in artifact_path.parents or not artifact_path.is_file():
            return Response(
                {"detail": "Artifact is not available."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            artifact_path.open("rb"),
            as_attachment=True,
            filename=artifact.name,
        )
