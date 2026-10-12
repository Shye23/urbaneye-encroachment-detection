from django.urls import path

from .views import (
    DetectionArtifactDownloadView,
    DetectionJobDetailView,
    DetectionJobListCreateView,
    DetectionReportListView,
)


urlpatterns = [
    path("", DetectionJobListCreateView.as_view(), name="detection-job-list"),
    path("reports/", DetectionReportListView.as_view(), name="detection-report-list"),
    path("<int:pk>/", DetectionJobDetailView.as_view(), name="detection-job-detail"),
    path(
        "<int:job_id>/artifacts/<int:artifact_id>/download/",
        DetectionArtifactDownloadView.as_view(),
        name="detection-artifact-download",
    ),
]
