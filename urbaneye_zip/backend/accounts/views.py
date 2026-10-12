from django.contrib.auth import authenticate
from .models import User

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdmin


from .serializers import RegisterSerializer, DepartmentOfficerSerializer, CreateDepartmentOfficerSerializer



class RegisterView(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "User registered successfully.",
                    "username": user.username,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "error": "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
class ProfileView(generics.RetrieveAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        full_name = (
            f"{user.first_name} {user.last_name}"
        ).strip()

        if not full_name:
            full_name = user.username

        role_labels = {
            "CITIZEN": "Citizen",
            "DEPARTMENT": "Department Officer",
            "ADMIN": "Administrator",
        }

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": full_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "role_label": role_labels.get(
                user.role,
                user.role,
            ),
            "status": (
                "Active Account"
                if user.is_active
                else "Inactive Account"
            ),
        })
class DepartmentOfficerListView(generics.ListAPIView):

    serializer_class = DepartmentOfficerSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return User.objects.filter(
            role="DEPARTMENT",
            is_active=True,
        ).order_by("first_name", "last_name")      
class CreateDepartmentOfficerView(generics.CreateAPIView):

    serializer_class = CreateDepartmentOfficerSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        officer = serializer.save()

        return Response(
            {
                "message": "Department Officer created successfully.",
                "officer": {
                    "id": officer.id,
                    "username": officer.username,
                    "full_name": (
                        f"{officer.first_name} "
                        f"{officer.last_name}"
                    ).strip() or officer.username,
                    "email": officer.email,
                    "role": officer.role,
                    "is_active": officer.is_active,
                },
            },
            status=status.HTTP_201_CREATED,
        )    