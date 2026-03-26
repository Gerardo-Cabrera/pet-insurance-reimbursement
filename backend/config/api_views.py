from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class HealthStatusSerializer(serializers.Serializer):
    service = serializers.CharField()
    status = serializers.CharField()
    database = serializers.CharField()
    claims_processing_mode = serializers.CharField()
    version = serializers.CharField()


token_request_serializer = inline_serializer(
    name="TokenRequest",
    fields={
        "email": serializers.EmailField(),
        "password": serializers.CharField(write_only=True),
    },
)

token_pair_response_serializer = inline_serializer(
    name="TokenPairResponse",
    fields={
        "access": serializers.CharField(),
        "refresh": serializers.CharField(),
    },
)

token_refresh_request_serializer = inline_serializer(
    name="TokenRefreshRequest",
    fields={
        "refresh": serializers.CharField(),
    },
)

token_refresh_response_serializer = inline_serializer(
    name="TokenRefreshResponse",
    fields={
        "access": serializers.CharField(),
    },
)


class TokenObtainPairSchemaView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Auth"],
        summary="Log in and get JWT tokens",
        description=(
            "Exchange user credentials for an access token and a refresh token. "
            "Use the access token in Swagger's Authorize dialog as `Bearer <token>`."
        ),
        request=token_request_serializer,
        responses={
            200: token_pair_response_serializer,
            401: OpenApiResponse(description="Invalid email or password."),
        },
        examples=[
            OpenApiExample(
                "Login request",
                value={
                    "email": "customer@example.com",
                    "password": "strongpass123",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshSchemaView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Auth"],
        summary="Refresh an access token",
        description="Generate a new access token using a valid refresh token.",
        request=token_refresh_request_serializer,
        responses={
            200: token_refresh_response_serializer,
            401: OpenApiResponse(description="Refresh token is invalid or expired."),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Health"],
        summary="Backend health check",
        description=(
            "Lightweight health endpoint intended for Docker Compose checks and quick "
            "manual verification from Swagger UI."
        ),
        responses={
            200: HealthStatusSerializer,
            503: OpenApiResponse(
                response=HealthStatusSerializer,
                description="The API is reachable but one of its dependencies is unhealthy.",
            ),
        },
    )
    def get(self, request):
        database_status = "ok"
        response_status = status.HTTP_200_OK
        overall_status = "ok"

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            database_status = "error"
            overall_status = "error"
            response_status = status.HTTP_503_SERVICE_UNAVAILABLE

        payload = {
            "service": "pet-insurance-backend",
            "status": overall_status,
            "database": database_status,
            "claims_processing_mode": settings.CLAIMS_PROCESSING_MODE.lower(),
            "version": settings.SPECTACULAR_SETTINGS["VERSION"],
        }
        return Response(payload, status=response_status)
