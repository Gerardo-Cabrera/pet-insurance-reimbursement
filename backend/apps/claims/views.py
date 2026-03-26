from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User

from .models import Claim
from .permissions import ClaimPermission
from .serializers import ClaimReviewSerializer, ClaimSerializer
from .services import approve_claim, reject_claim


@extend_schema_view(
    list=extend_schema(
        tags=["Claims"],
        summary="List claims",
        description=(
            "Customers only see their own claims. Support and admin users can inspect "
            "the full review queue."
        ),
    ),
    retrieve=extend_schema(
        tags=["Claims"],
        summary="Retrieve a claim",
    ),
    create=extend_schema(
        tags=["Claims"],
        summary="Create a claim",
        description=(
            "Upload an invoice for one of the customer's insured pets. The claim is "
            "stored in `PROCESSING` first, then automatic validation moves it to "
            "`IN_REVIEW` or `REJECTED`."
        ),
        responses={
            201: ClaimSerializer,
            400: OpenApiResponse(
                description=(
                    "Validation error, such as duplicate invoice hash or trying to use a "
                    "pet that belongs to another customer."
                )
            ),
        },
        examples=[
            OpenApiExample(
                "Create claim request",
                value={
                    "pet": 1,
                    "invoice_date": "2026-02-10",
                    "date_of_event": "2026-02-09",
                    "amount": "129.90",
                },
                request_only=True,
                description="Submit this request as multipart/form-data and attach `invoice`.",
            )
        ],
    ),
)
class ClaimViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Claim.objects.none()
    serializer_class = ClaimSerializer
    permission_classes = [ClaimPermission]
    filterset_fields = ("status", "pet")
    search_fields = ("owner__email", "pet__name", "invoice_hash")
    ordering_fields = ("created_at", "amount", "status")

    def get_queryset(self):
        queryset = Claim.objects.select_related("owner", "pet", "reviewed_by")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()

        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()

        if user.role in {User.Role.SUPPORT, User.Role.ADMIN}:
            return queryset
        return queryset.filter(owner=user)

    @extend_schema(
        tags=["Claims"],
        summary="Approve a claim",
        description="Approve a claim that is already in `IN_REVIEW`.",
        request=ClaimReviewSerializer,
        responses={
            200: ClaimSerializer,
            400: OpenApiResponse(description="The claim is not in review."),
            403: OpenApiResponse(description="Only support and admin users can approve."),
        },
    )
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        claim = self.get_object()
        serializer = ClaimReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            claim = approve_claim(
                claim,
                reviewer=request.user,
                notes=serializer.validated_data.get("review_notes", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(claim).data)

    @extend_schema(
        tags=["Claims"],
        summary="Reject a claim",
        description=(
            "Reject a claim that is already in `IN_REVIEW`. `review_notes` should explain "
            "the rejection reason."
        ),
        request=ClaimReviewSerializer,
        responses={
            200: ClaimSerializer,
            400: OpenApiResponse(description="The claim is not in review or notes are missing."),
            403: OpenApiResponse(description="Only support and admin users can reject."),
        },
        examples=[
            OpenApiExample(
                "Reject claim request",
                value={"review_notes": "Invoice total does not match the supporting evidence."},
                request_only=True,
            )
        ],
    )
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        claim = self.get_object()
        serializer = ClaimReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            claim = reject_claim(
                claim,
                reviewer=request.user,
                notes=serializer.validated_data.get("review_notes", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(claim).data)
