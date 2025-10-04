from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import secrets


User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    telegram_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=64, null=True, blank=True)
    phone_number = models.CharField(max_length=32, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Profile({self.user_id}, tg={self.telegram_username or self.telegram_id})"


class OTPLoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_sessions")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_verified"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"OTP(user={self.user_id}, verified={self.is_verified})"

    @staticmethod
    def generate_code() -> str:
        return f"{secrets.randbelow(1000000):06d}"

    @classmethod
    def create_for_user(cls, user: User, ttl_seconds: int = 300):
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)
        return cls.objects.create(
            user=user,
            code=cls.generate_code(),
            expires_at=expires_at,
        )

# Create your models here.
