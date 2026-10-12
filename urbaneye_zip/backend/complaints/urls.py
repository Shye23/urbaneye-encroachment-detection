from django.urls import path

from .views import (
    ComplaintListCreateView,
    ComplaintDetailView,
    ComplaintStatusUpdateView,
    ComplaintImageUploadView,
    DangerZoneListView,

    AdminComplaintListView,

    EncroachmentCaseListView,
    EncroachmentCaseAssignView,

    DepartmentAssignedCaseListView,
    DepartmentCaseActionView,

    AdminEncroachmentCaseListView,
    AdminCaseReportView,
    AdminAssignOfficerView,
)


urlpatterns = [

    # =====================================================
    # CITIZEN - COMPLAINTS
    # =====================================================

    path(
        "",
        ComplaintListCreateView.as_view(),
        name="complaint-list-create",
    ),

    path(
        "<int:pk>/",
        ComplaintDetailView.as_view(),
        name="complaint-detail",
    ),

    path(
        "<int:pk>/status/",
        ComplaintStatusUpdateView.as_view(),
        name="complaint-status-update",
    ),

    path(
        "<int:pk>/images/",
        ComplaintImageUploadView.as_view(),
        name="complaint-image-upload",
    ),


    # =====================================================
    # CITIZEN - DANGER ZONES
    # =====================================================

    path(
        "danger-zones/",
        DangerZoneListView.as_view(),
        name="danger-zone-list",
    ),


    # =====================================================
    # ADMIN - COMPLAINTS
    # =====================================================

    path(
        "admin/complaints/",
        AdminComplaintListView.as_view(),
        name="admin-complaint-list",
    ),


    # =====================================================
    # ADMIN - ENCROACHMENT CASES
    # =====================================================

    path(
        "encroachment-cases/",
        EncroachmentCaseListView.as_view(),
        name="encroachment-case-list",
    ),

    # Old/general assignment endpoint
    path(
        "encroachment-cases/<int:pk>/assign/",
        EncroachmentCaseAssignView.as_view(),
        name="encroachment-case-assign",
    ),


    # =====================================================
    # ADMIN - ENCROACHMENT CASE LIST
    # =====================================================

    path(
        "admin/encroachment-cases/",
        AdminEncroachmentCaseListView.as_view(),
        name="admin-encroachment-cases",
    ),


    # =====================================================
    # ADMIN - CASE REPORT
    # =====================================================

    path(
        "admin/encroachment-cases/<int:pk>/report/",
        AdminCaseReportView.as_view(),
        name="admin-case-report",
    ),


    # =====================================================
    # ADMIN - ASSIGN OFFICER
    # =====================================================

    path(
        "admin/encroachment-cases/<int:pk>/assign/",
        AdminAssignOfficerView.as_view(),
        name="admin-assign-officer",
    ),


    # =====================================================
    # DEPARTMENT OFFICER
    # =====================================================

    path(
        "department/assigned-cases/",
        DepartmentAssignedCaseListView.as_view(),
        name="department-assigned-cases",
    ),

    path(
        "department/assigned-cases/<int:pk>/actions/",
        DepartmentCaseActionView.as_view(),
        name="department-case-actions",
    ),
]