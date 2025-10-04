from django.urls import path
from . import views


urlpatterns = [
    path("auth/request_code/", views.request_code, name="auth_request_code"),
    path("auth/verify_code/", views.verify_code, name="auth_verify_code"),
    path("login/", views.login_page, name="login_page"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("debug-codes/", views.debug_codes, name="debug_codes"),
    path("logout/", views.logout_view, name="logout"),
]


