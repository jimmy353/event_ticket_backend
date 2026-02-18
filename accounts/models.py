from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import random


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        extra_fields.setdefault("is_organizer", True)
        extra_fields.setdefault("is_customer", False)

        extra_fields.setdefault("is_verified", True)  # ✅ superuser verified

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    # roles
    is_customer = models.BooleanField(default=True)
    is_organizer = models.BooleanField(default=False)

    # verification
    is_verified = models.BooleanField(default=False)  # ✅ email verified or not

    # system fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class EmailOTP(models.Model):
    PURPOSE_CHOICES = (
        ("verify", "Verify Email"),
        ("reset", "Reset Password"),
    )

    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = str(random.randint(100000, 999999))  # 6-digit OTP

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # expires in 10 minutes

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} - {self.otp_code} ({self.purpose})"


class OrganizerRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="organizer_request"
    )

    company_name = models.CharField(max_length=255)
    momo_number = models.CharField(max_length=50)

    id_document = models.FileField(upload_to="organizer_ids/")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"
