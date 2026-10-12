from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError

from accounts.permissions import IsAdmin, IsDepartmentOfficer
from accounts.models import User

from .models import (
    Complaint,
    ComplaintStatusHistory,
    DangerZone,
    EncroachmentCase,
    EncroachmentCaseActionHistory,
   
)

from .serializers import (
    ComplaintSerializer,
    ComplaintImageSerializer,
    DangerZoneSerializer,
    EncroachmentCaseSerializer,
    DepartmentCaseSerializer,
    EncroachmentCaseActionHistorySerializer,
    AdminCaseReportSerializer,
    AssignOfficerSerializer,
     AdminCaseReportSerializer,
       
)


# =========================================================
# CITIZEN - COMPLAINTS
# =========================================================

class ComplaintListCreateView(generics.ListCreateAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Complaint.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )


class ComplaintDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Complaint.objects.filter(
            user=self.request.user
        )


class ComplaintStatusUpdateView(generics.UpdateAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Complaint.objects.filter(
            user=self.request.user
        )

    def update(self, request, *args, **kwargs):

        complaint = self.get_object()

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "Status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = [
            "PENDING",
            "UNDER_REVIEW",
            "VERIFIED",
            "REJECTED",
            "RESOLVED",
        ]

        if new_status not in valid_statuses:
            return Response(
                {"error": "Invalid status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = complaint.status

        complaint.status = new_status
        complaint.save()

        if old_status != new_status:
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                status=new_status,
                changed_by=request.user,
            )

        serializer = self.get_serializer(complaint)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ComplaintImageUploadView(generics.CreateAPIView):

    serializer_class = ComplaintImageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        complaint_id = self.kwargs["pk"]

        try:
            complaint = Complaint.objects.get(
                pk=complaint_id,
                user=self.request.user,
            )
        except Complaint.DoesNotExist:
            raise NotFound(
                "Complaint not found."
            )

        serializer.save(
            complaint=complaint
        )


# =========================================================
# CITIZEN - DANGER ZONES
# =========================================================

class DangerZoneListView(generics.ListAPIView):

    serializer_class = DangerZoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return DangerZone.objects.filter(
            is_active=True
        ).order_by("-updated_at")


# =========================================================
# ADMIN - ALL COMPLAINTS
# =========================================================

class AdminComplaintListView(generics.ListAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):

        return Complaint.objects.all().order_by(
            "-created_at"
        )


# =========================================================
# ADMIN - ENCROACHMENT CASES
# =========================================================

class EncroachmentCaseListView(generics.ListCreateAPIView):

    serializer_class = EncroachmentCaseSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):

        return EncroachmentCase.objects.all().order_by(
            "-created_at"
        )

    def perform_create(self, serializer):

        serializer.save()


class AdminEncroachmentCaseListView(generics.ListAPIView):

    serializer_class = EncroachmentCaseSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):

        return EncroachmentCase.objects.all().order_by(
            "-created_at"
        )


# =========================================================
# ADMIN - CASE REPORT
# =========================================================

class AdminCaseReportView(generics.RetrieveAPIView):

    serializer_class = AdminCaseReportSerializer
    permission_classes = [IsAdmin]

    queryset = EncroachmentCase.objects.all()


# =========================================================
# ADMIN - ASSIGN OFFICER
# =========================================================

class AdminAssignOfficerView(generics.UpdateAPIView):

    serializer_class = AssignOfficerSerializer
    permission_classes = [IsAdmin]

    queryset = EncroachmentCase.objects.all()

    def update(self, request, *args, **kwargs):

        case = self.get_object()

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        officer_id = serializer.validated_data.get(
            "officer_id"
        )

        if not officer_id:
            return Response(
                {
                    "error": "officer_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            officer = User.objects.get(
                id=officer_id,
                role="DEPARTMENT",
            )

        except User.DoesNotExist:

            return Response(
                {
                    "error": "Department officer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # IMPORTANT:
        # Model field is assigned_to
        case.assigned_to = officer

        if case.status == "OPEN":
            case.status = "ASSIGNED"

        case.save()

        return Response(
            {
                "message": "Officer assigned successfully.",
                "case_id": case.id,
                "case_number": case.case_number,
                "assigned_officer": {
                    "id": officer.id,
                    "username": officer.username,
                    "full_name": (
                        f"{officer.first_name} "
                        f"{officer.last_name}"
                    ).strip() or officer.username,
                },
                "status": case.status,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# DEPARTMENT OFFICER - ASSIGNED CASES
# =========================================================

class DepartmentAssignedCaseListView(generics.ListAPIView):

    serializer_class = DepartmentCaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print("========== DEPARTMENT DEBUG ==========")
        print("USER:", self.request.user)
        print("USER ID:", self.request.user.id)
        print("USERNAME:", self.request.user.username)
        print("ROLE:", self.request.user.role)
        print("AUTHENTICATED:", self.request.user.is_authenticated)
        print("=======================================")

        return EncroachmentCase.objects.filter(
            assigned_to=self.request.user
        ).order_by("-created_at")

# =========================================================
# DEPARTMENT OFFICER - CASE ACTIONS
# =========================================================

class DepartmentCaseActionView(
    generics.ListCreateAPIView
):

    serializer_class = EncroachmentCaseActionHistorySerializer
    permission_classes = [IsDepartmentOfficer]

    def get_queryset(self):

        case_id = self.kwargs["pk"]

        return EncroachmentCaseActionHistory.objects.filter(
            case_id=case_id,
            case__assigned_to=self.request.user,
        ).order_by(
            "-created_at"
        )

    def perform_create(self, serializer):

        case_id = self.kwargs["pk"]

        try:

            case = EncroachmentCase.objects.get(
                pk=case_id,
                assigned_to=self.request.user,
            )

        except EncroachmentCase.DoesNotExist:

            raise NotFound(
                "Case not found or not assigned to you."
            )

        action = self.request.data.get(
            "action"
        )

        valid_actions = [
            "STARTED",
            "INSPECTION",
            "VERIFICATION",
            "NOTICE_ISSUED",
            "ACTION_TAKEN",
            "RESOLVED",
        ]

        if action not in valid_actions:

            raise ValidationError(
                {
                    "action": "Invalid action."
                }
            )

        serializer.save(
            case=case,
            performed_by=self.request.user,
        )

        # Update case status

        if action == "RESOLVED":

            case.status = "RESOLVED"

        else:

            case.status = "IN_PROGRESS"

        case.save()


# =========================================================
# OPTIONAL - OLD ASSIGN URL COMPATIBILITY
# =========================================================
# Agar frontend kahin /encroachment-cases/<id>/assign/
# call kar raha hai, to ye class us URL ko support karegi.

class EncroachmentCaseAssignView(
    AdminAssignOfficerView
):
    pass

