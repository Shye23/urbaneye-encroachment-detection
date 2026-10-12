from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        CITIZEN = "CITIZEN", "Citizen"
        DEPARTMENT = "DEPARTMENT", "Department"
        ADMIN = "ADMIN", "Admin"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITIZEN,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    is_anonymous = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.username} ({self.role})"