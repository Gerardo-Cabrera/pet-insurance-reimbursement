from datetime import date, timedelta

import pytest
from rest_framework import status

from apps.claims.models import Claim


@pytest.mark.django_db
def test_customer_can_create_pet(api_client, customer):
    api_client.force_authenticate(user=customer)

    response = api_client.post(
        "/api/pets/",
        {
            "name": "Rocco",
            "species": "DOG",
            "birth_date": "2022-01-01",
            "coverage_start": "2026-03-01",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["owner_email"] == customer.email
    assert response.data["coverage_end"] == str(date(2026, 3, 1) + timedelta(days=365))


@pytest.mark.django_db
def test_customer_only_sees_own_pets(api_client, customer, customer_pet, other_pet):
    api_client.force_authenticate(user=customer)

    response = api_client.get("/api/pets/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == customer_pet.id


@pytest.mark.django_db
def test_support_can_list_all_pets(api_client, support_user, customer_pet, other_pet):
    api_client.force_authenticate(user=support_user)

    response = api_client.get("/api/pets/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_support_cannot_create_pet(api_client, support_user):
    api_client.force_authenticate(user=support_user)

    response = api_client.post(
        "/api/pets/",
        {
            "name": "Nope",
            "species": "DOG",
            "birth_date": "2022-01-01",
            "coverage_start": "2026-03-01",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_can_delete_pet_without_claims(api_client, customer, customer_pet):
    api_client.force_authenticate(user=customer)

    response = api_client.delete(f"/api/pets/{customer_pet.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_customer_cannot_delete_pet_with_claim_history(
    api_client,
    customer,
    customer_pet,
    invoice_file,
):
    api_client.force_authenticate(user=customer)
    claim_response = api_client.post(
        "/api/claims/",
        {
            "pet": customer_pet.id,
            "invoice": invoice_file,
            "invoice_date": "2026-02-10",
            "date_of_event": "2026-02-09",
            "amount": "49.00",
        },
        format="multipart",
    )

    assert claim_response.status_code == status.HTTP_201_CREATED
    assert Claim.objects.filter(pet=customer_pet).exists()

    response = api_client.delete(f"/api/pets/{customer_pet.id}/")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "claims history" in response.data["detail"]
