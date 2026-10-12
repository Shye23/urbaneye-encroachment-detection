from rest_framework import serializers

from .models import (
    Complaint,
    ComplaintImage,
    ComplaintStatusHistory,
    DangerZone,
    EncroachmentCase,
    EncroachmentCaseActionHistory,
)


# =========================================================
# COMPLAINT IMAGE
# =========================================================

class ComplaintImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ComplaintImage

        fields = [
            "id",
            "image",
            "uploaded_at",
        ]

        read_only_fields = [
            "id",
            "uploaded_at",
        ]

# =========================================================
# COMPLAINT STATUS HISTORY
# =========================================================

class ComplaintStatusHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ComplaintStatusHistory

        fields = [
            "id",
            "status",
            "changed_at",
            "changed_by",
        ]

        read_only_fields = [
            "id",
            "changed_at",
            "changed_by",
        ]


# =========================================================
# COMPLAINT
# =========================================================

class ComplaintSerializer(serializers.ModelSerializer):

    images = ComplaintImageSerializer(
        many=True,
        read_only=True,
    )

    status_history = ComplaintStatusHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Complaint

        fields = [
            "id",
            "title",
            "description",
            "category",
            "latitude",
            "longitude",
            "address",
            "status",
            "is_anonymous",
            "created_at",
            "updated_at",
            "images",
            "status_history",
        ]

        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
            "images",
            "status_history",
        ]


# =========================================================
# DANGER ZONE
# =========================================================

class DangerZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = DangerZone

        fields = [
            "id",
            "name",
            "description",
            "risk_level",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


# =========================================================
# ADMIN ENCROACHMENT CASE
# =========================================================

class EncroachmentCaseSerializer(serializers.ModelSerializer):

    assigned_officer_name = serializers.SerializerMethodField()

    class Meta:
        model = EncroachmentCase

        fields = [
            "id",
            "case_number",
            "source",
            "complaint",
            "assigned_to",
            "assigned_officer_name",
            "title",
            "description",
            "address",
            "latitude",
            "longitude",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "assigned_officer_name",
            "created_at",
            "updated_at",
        ]

    def get_assigned_officer_name(self, obj):

        if not obj.assigned_to:
            return None

        full_name = (
            f"{obj.assigned_to.first_name} "
            f"{obj.assigned_to.last_name}"
        ).strip()

        return (
            full_name
            or obj.assigned_to.username
        )


# =========================================================
# DEPARTMENT OFFICER CASE
# PRIVACY SAFE
# =========================================================

class DepartmentCaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = EncroachmentCase

        fields = [
            "id",
            "case_number",
            "source",
            "title",
            "description",
            "address",
            "latitude",
            "longitude",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "case_number",
            "source",
            "title",
            "description",
            "address",
            "latitude",
            "longitude",
            "status",
            "created_at",
            "updated_at",
        ]


# =========================================================
# OFFICER ACTION HISTORY
# =========================================================

class EncroachmentCaseActionHistorySerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = EncroachmentCaseActionHistory

        fields = [
            "id",
            "case",
            "action",
            "remarks",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "case",
            "created_at",
        ]


# =========================================================
# ADMIN COMPLETE CASE REPORT
# =========================================================

class AdminCaseReportSerializer(serializers.ModelSerializer):

    assigned_officer_name = serializers.SerializerMethodField()

    action_history = EncroachmentCaseActionHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = EncroachmentCase

        fields = [
            "id",
            "case_number",
            "source",
            "title",
            "description",
            "address",
            "latitude",
            "longitude",
            "status",
            "assigned_officer_name",
            "action_history",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "case_number",
            "source",
            "title",
            "description",
            "address",
            "latitude",
            "longitude",
            "status",
            "assigned_officer_name",
            "action_history",
            "created_at",
            "updated_at",
        ]

    def get_assigned_officer_name(self, obj):

        if not obj.assigned_to:
            return None

        full_name = (
            f"{obj.assigned_to.first_name} "
            f"{obj.assigned_to.last_name}"
        ).strip()

        return (
            full_name
            or obj.assigned_to.username
        )


# =========================================================
# ADMIN ASSIGN OFFICER
# =========================================================

class AssignOfficerSerializer(serializers.Serializer):

    officer_id = serializers.IntegerField()

    def validate_officer_id(self, value):

        from accounts.models import User

        try:
            officer = User.objects.get(
                id=value,
                role="DEPARTMENT",
                is_active=True,
            )

        except User.DoesNotExist:

            raise serializers.ValidationError(
                "Invalid department officer."
            )

        return officer.id