from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Claim
from .services import calculate_file_hash, dispatch_claim_processing


DUPLICATE_INVOICE_MESSAGE = "This invoice file has already been submitted."


class ClaimSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    pet_name = serializers.CharField(source="pet.name", read_only=True)

    class Meta:
        model = Claim
        fields = (
            "id",
            "owner",
            "owner_email",
            "pet",
            "pet_name",
            "invoice",
            "invoice_hash",
            "invoice_date",
            "date_of_event",
            "amount",
            "status",
            "review_notes",
            "processing_summary",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_email",
            "pet_name",
            "invoice_hash",
            "status",
            "review_notes",
            "processing_summary",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        )

    def validate_pet(self, pet):
        request = self.context["request"]
        if request.user.role == request.user.Role.CUSTOMER and pet.owner_id != request.user.id:
            raise serializers.ValidationError("You can only create claims for your own pets.")
        return pet

    def create(self, validated_data):
        invoice = validated_data["invoice"]
        invoice_hash = calculate_file_hash(invoice)

        if Claim.objects.filter(invoice_hash=invoice_hash).exists():
            raise serializers.ValidationError({"invoice": DUPLICATE_INVOICE_MESSAGE})

        pet = validated_data["pet"]
        try:
            with transaction.atomic():
                claim = Claim.objects.create(
                    owner=pet.owner,
                    invoice_hash=invoice_hash,
                    status=Claim.Status.PROCESSING,
                    processing_summary="Claim received and queued for automatic validation.",
                    **validated_data,
                )
                if settings.CLAIMS_PROCESSING_MODE.lower() != "sync":
                    transaction.on_commit(lambda: dispatch_claim_processing(claim.id))
        except IntegrityError as exc:
            if "invoice_hash" in str(exc):
                raise serializers.ValidationError(
                    {"invoice": DUPLICATE_INVOICE_MESSAGE}
                ) from exc
            raise

        if settings.CLAIMS_PROCESSING_MODE.lower() == "sync":
            dispatch_claim_processing(claim.id)
            claim.refresh_from_db()
        return claim


class ClaimReviewSerializer(serializers.Serializer):
    review_notes = serializers.CharField(required=False, allow_blank=True)
