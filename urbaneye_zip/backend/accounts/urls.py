from django.urls import path

from .views import RegisterView, LoginView,ProfileView,  DepartmentOfficerListView,   CreateDepartmentOfficerView

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),
    path("profile/", ProfileView.as_view(), name="profile"),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh"
    ),
    path(
    "admin/department-officers/",
    DepartmentOfficerListView.as_view(),
    name="admin-department-officers",
),
path(
    "admin/department-officers/create/",
    CreateDepartmentOfficerView.as_view(),
    name="admin-create-department-officer",
),

]