from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import OrganizerRequest, EmailOTP, OrganizerSettings

User = get_user_model()


# ==========================
# REGISTER (EMAIL + PASSWORD ONLY)
# ==========================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
        ]

    def validate(self, attrs):
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.get("email")

        user = User(email=email)
        user.set_password(password)

        # Default flags
        user.is_customer = True
        user.is_organizer = False
        user.is_verified = False

        user.save()

        # Create OTP for verification
        EmailOTP.objects.filter(
            email=email,
            purpose="verify",
            is_used=False
        ).delete()

        EmailOTP.objects.create(
            email=email,
            purpose="verify"
        )

        return user


# ==========================
# VERIFY OTP
# ==========================
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            otp_obj = EmailOTP.objects.get(
                email=email,
                otp_code=otp,
                purpose="verify",
                is_used=False
            )
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP"})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired. Please request a new one."})

        attrs["otp_obj"] = otp_obj
        return attrs


# ==========================
# RESEND OTP
# ==========================
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ==========================
# FORGOT PASSWORD
# ==========================
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email")
        return value


# ==========================
# RESET PASSWORD
# ==========================
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")
        new_password = attrs.get("new_password")
        new_password2 = attrs.get("new_password2")

        if new_password != new_password2:
            raise serializers.ValidationError({"new_password": "Passwords do not match"})

        validate_password(new_password)

        try:
            otp_obj = EmailOTP.objects.get(
                email=email,
                otp_code=otp,
                purpose="reset",
                is_used=False
            )
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP"})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired. Request a new one."})

        attrs["otp_obj"] = otp_obj
        return attrs


# ==========================
# PROFILE
# ==========================
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "is_customer",
            "is_organizer",
            "is_verified",
        ]


# ==========================
# ORGANIZER REQUEST (WEB DASHBOARD)
# ==========================
class OrganizerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerRequest
        fields = [
            "company_name",
            "momo_number",
            "id_document",
            "status",
        ]


# ==========================
# ORGANIZER SETTINGS (WEB DASHBOARD)
# ==========================
class OrganizerSettingsSerializer(serializers.ModelSerializer):

    logo = serializers.ImageField(required=False)
    banner = serializers.ImageField(required=False)

    class Meta:
        model = OrganizerSettings
        fields = [
            "business_name",
            "business_phone",
            "description",
            "logo",
            "banner",
            "payout_provider",
            "payout_phone",
            "auto_payout",
        ]

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.is_organizer:
            raise serializers.ValidationError("Only organizers can update settings.")

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user

        settings, created = OrganizerSettings.objects.get_or_create(
            user=user,
            defaults=validated_data
        )

        if not created:
            for attr, value in validated_data.items():
                setattr(settings, attr, value)
            settings.save()

        return settings

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance