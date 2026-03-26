from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
import pytest
from rest_framework import status

from apps.claims import serializers as claim_serializers
from apps.claims.models import Claim


@pytest.mark.django_db
def test_customer_can_create_claim_and_it_enters_review(
    api_client,
    customer,
    claim_payload,
):
    api_client.force_authenticate(user=customer)

    response = api_client.post("/api/claims/", claim_payload, format="multipart")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == Claim.Status.IN_REVIEW
    assert "validated" in response.data["processing_summary"].lower()


@pytest.mark.django_db
def test_thread_mode_returns_processing_during_creation(
    api_client,
    customer,
    claim_payload,
    settings,
    monkeypatch,
):
    api_client.force_authenticate(user=customer)
    settings.CLAIMS_PROCESSING_MODE = "thread"
    settings.CLAIMS_PROCESSING_DELAY_SECONDS = 0
    monkeypatch.setattr(
        claim_serializers,
        "dispatch_claim_processing",
        lambda claim_id: None,
    )

    response = api_client.post("/api/claims/", claim_payload, format="multipart")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == Claim.Status.PROCESSING
    assert "queued" in response.data["processing_summary"].lower()


@pytest.mark.django_db
def test_duplicate_invoice_hash_is_rejected(
    api_client,
    customer,
    claim_payload,
    customer_pet,
):
    api_client.force_authenticate(user=customer)

    first_response = api_client.post("/api/claims/", claim_payload, format="multipart")
    assert first_response.status_code == status.HTTP_201_CREATED

    second_file = SimpleUploadedFile(
        "invoice-copy.pdf",
        b"fake-pdf-content",
        content_type="application/pdf",
    )
    second_response = api_client.post(
        "/api/claims/",
        {
            "pet": customer_pet.id,
            "invoice": second_file,
            "invoice_date": "2026-02-10",
            "date_of_event": "2026-02-09",
            "amount": "129.90",
        },
        format="multipart",
    )

    assert second_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invoice" in second_response.data


@pytest.mark.django_db
def test_duplicate_invoice_integrity_error_is_returned_as_validation_error(
    api_client,
    customer,
    claim_payload,
    monkeypatch,
):
    api_client.force_authenticate(user=customer)
    exists_results = iter([False, True])

    def duplicate_create(*args, **kwargs):
        raise IntegrityError("database constraint violated")

    class FilterResult:
        def exists(self):
            return next(exists_results)

    monkeypatch.setattr(Claim.objects, "create", duplicate_create)
    monkeypatch.setattr(Claim.objects, "filter", lambda *args, **kwargs: FilterResult())

    response = api_client.post("/api/claims/", claim_payload, format="multipart")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invoice" in response.data
    assert "already been submitted" in str(response.data["invoice"]).lower()


@pytest.mark.django_db
def test_customer_cannot_create_claim_for_another_pet(
    api_client,
    customer,
    other_pet,
    invoice_file,
):
    api_client.force_authenticate(user=customer)

    response = api_client.post(
        "/api/claims/",
        {
            "pet": other_pet.id,
            "invoice": invoice_file,
            "invoice_date": "2026-02-10",
            "date_of_event": "2026-02-09",
            "amount": "49.00",
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "pet" in response.data


@pytest.mark.django_db
def test_claim_outside_coverage_is_rejected_at_validation(
    api_client,
    customer,
    customer_pet,
    invoice_file,
):
    api_client.force_authenticate(user=customer)

    response = api_client.post(
        "/api/claims/",
        {
            "pet": customer_pet.id,
            "invoice": invoice_file,
            "invoice_date": "2028-02-10",
            "date_of_event": "2028-02-09",
            "amount": "49.00",
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == Claim.Status.REJECTED
    assert "coverage period" in response.data["review_notes"].lower()


@pytest.mark.django_db
def test_support_can_approve_claim(api_client, customer, support_user, claim_payload):
    api_client.force_authenticate(user=customer)
    create_response = api_client.post("/api/claims/", claim_payload, format="multipart")
    claim_id = create_response.data["id"]

    api_client.force_authenticate(user=support_user)
    review_response = api_client.post(
        f"/api/claims/{claim_id}/approve/",
        {"review_notes": "Everything looks correct."},
        format="json",
    )

    assert review_response.status_code == status.HTTP_200_OK
    assert review_response.data["status"] == Claim.Status.APPROVED
    assert review_response.data["review_notes"] == "Everything looks correct."


@pytest.mark.django_db
def test_reject_requires_notes(api_client, customer, support_user, claim_payload):
    api_client.force_authenticate(user=customer)
    create_response = api_client.post("/api/claims/", claim_payload, format="multipart")
    claim_id = create_response.data["id"]

    api_client.force_authenticate(user=support_user)
    review_response = api_client.post(
        f"/api/claims/{claim_id}/reject/",
        {"review_notes": ""},
        format="json",
    )

    assert review_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_customer_cannot_approve_claim(api_client, customer, claim_payload):
    api_client.force_authenticate(user=customer)
    create_response = api_client.post("/api/claims/", claim_payload, format="multipart")
    claim_id = create_response.data["id"]

    review_response = api_client.post(
        f"/api/claims/{claim_id}/approve/",
        {"review_notes": "Trying to cheat."},
        format="json",
    )

    assert review_response.status_code == status.HTTP_403_FORBIDDEN
