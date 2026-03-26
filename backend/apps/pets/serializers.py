from rest_framework import serializers

from .models import Pet


class PetSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    claim_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Pet
        fields = (
            "id",
            "owner",
            "owner_email",
            "name",
            "species",
            "birth_date",
            "coverage_start",
            "coverage_end",
            "claim_count",
            "created_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_email",
            "coverage_end",
            "claim_count",
            "created_at",
        )
