import pytest
from rest_framework import status


@pytest.mark.django_db
def test_user_can_register(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "new@example.com",
            "first_name": "Grace",
            "last_name": "Hopper",
            "password": "strongpass123",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["email"] == "new@example.com"
    assert response.data["role"] == "CUSTOMER"


@pytest.mark.django_db
def test_authenticated_user_can_fetch_profile(api_client, customer):
    api_client.force_authenticate(user=customer)

    response = api_client.get("/api/auth/me/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == customer.email
