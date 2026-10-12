from django.conf import settings
from django.db import models


class Complaint(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("UNDER_REVIEW", "Under Review"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
        ("RESOLVED", "Resolved"),
    ]

    CATEGORY_CHOICES = [
        ("ROADSIDE", "Roadside"),
        ("FOOTPATH", "Footpath"),
        ("PUBLIC_LAND", "Public Land"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="ENCROACHMENT",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    address = models.CharField(
        max_length=500,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    is_anonymous = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.status}"


class ComplaintImage(models.Model):

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="complaints/%Y/%m/%d/"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Complaint #{self.complaint.id}"


class ComplaintStatusHistory(models.Model):

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    status = models.CharField(
        max_length=20,
        choices=Complaint.STATUS_CHOICES,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_status_changes",
    )

    changed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.complaint.title} - {self.status}"


class DangerZone(models.Model):

    RISK_CHOICES = [
        ("HIGH", "High Risk"),
        ("MEDIUM", "Medium Risk"),
        ("LOW", "Low Risk"),
    ]

    name = models.CharField(
        max_length=200
    )

    description = models.TextField()

    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        default="MEDIUM",
    )

    address = models.CharField(
        max_length=500,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} - {self.risk_level}"


class EncroachmentCase(models.Model):

    SOURCE_CHOICES = [
        ("COMPLAINT", "Complaint"),
        ("DETECTION", "Detection"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("UNDER_REVIEW", "Under Review"),
        ("ASSIGNED", "Assigned"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    ]

    case_number = models.CharField(
        max_length=50,
        unique=True,
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="COMPLAINT",
    )

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encroachment_cases",
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    address = models.CharField(
        max_length=500,
        blank=True,
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    # Department Officer assigned to this case
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_encroachment_cases",
        limit_choices_to={
            "role": "DEPARTMENT"
        },
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case_number} - {self.title}"
class EncroachmentCaseActionHistory(models.Model):

    ACTION_CHOICES = [
        ("STARTED", "Started"),
        ("INSPECTION", "Inspection"),
        ("VERIFICATION", "Verification"),
        ("NOTICE_ISSUED", "Notice Issued"),
        ("ACTION_TAKEN", "Action Taken"),
        ("RESOLVED", "Resolved"),
    ]

    case = models.ForeignKey(
        EncroachmentCase,
        on_delete=models.CASCADE,
        related_name="action_history",
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
    )

    remarks = models.TextField(
        blank=True,
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encroachment_actions",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case.case_number} - {self.action}"    