from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Only ADMIN users can access.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsDepartmentOfficer(BasePermission):
    """
    Only DEPARTMENT users can access.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "DEPARTMENT"
        )


class IsCitizen(BasePermission):
    """
    Only CITIZEN users can access.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "CITIZEN"
        )


class IsAdminOrDepartmentOfficer(BasePermission):
    """
    ADMIN and DEPARTMENT users can access.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["ADMIN", "DEPARTMENT"]
        )