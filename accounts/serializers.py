from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import OrganizerRequest

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    role = serializers.CharField(write_only=True, required=True)

    # organizer extra fields
    company_name = serializers.CharField(write_only=True, required=False)
    momo_number = serializers.CharField(write_only=True, required=False)
    id_document = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "password",
            "password2",
            "role",
            "company_name",
            "momo_number",
            "id_document",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})

        validate_password(attrs["password"])

        role = attrs.get("role")
        if role not in ["customer", "organizer"]:
            raise serializers.ValidationError({"role": "Role must be customer or organizer"})

        # organizer required fields
        if role == "organizer":
            if not attrs.get("company_name"):
                raise serializers.ValidationError({"company_name": "Company name is required"})
            if not attrs.get("momo_number"):
                raise serializers.ValidationError({"momo_number": "MoMo number is required"})
            if not attrs.get("id_document"):
                raise serializers.ValidationError({"id_document": "ID document is required"})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")

        role = validated_data.pop("role")

        company_name = validated_data.pop("company_name", None)
        momo_number = validated_data.pop("momo_number", None)
        id_document = validated_data.pop("id_document", None)

        user = User(**validated_data)
        user.set_password(password)

        # default customer
        user.is_customer = True
        user.is_organizer = False

        # organizer signup: disable customer role
        if role == "organizer":
            user.is_customer = False
            user.is_organizer = False

        user.save()

        # create organizer request
        if role == "organizer":
            OrganizerRequest.objects.create(
                user=user,
                company_name=company_name,
                momo_number=momo_number,
                id_document=id_document,
                status="pending"
            )

        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "is_customer",
            "is_organizer",
        ]


class OrganizerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerRequest
        fields = [
            "company_name",
            "momo_number",
            "id_document",
            "status",
        ]