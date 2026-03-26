from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer


@extend_schema(
    tags=["Auth"],
    summary="Register a customer account",
    description=(
        "Create a new user account. Public self-registration always creates a "
        "`CUSTOMER` user."
    ),
    request=RegisterSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(description="Validation error, such as duplicate email."),
    },
    examples=[
        OpenApiExample(
            "Register request",
            value={
                "email": "customer@example.com",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "password": "strongpass123",
            },
            request_only=True,
        )
    ],
)
class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema(
    tags=["Auth"],
    summary="Get the authenticated user profile",
    description="Return the current authenticated user and role information.",
    responses={200: UserSerializer, 401: OpenApiResponse(description="JWT required.")},
)
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
