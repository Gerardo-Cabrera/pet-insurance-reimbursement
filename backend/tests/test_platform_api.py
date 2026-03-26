import pytest
from rest_framework import status


@pytest.mark.django_db
def test_health_endpoint_is_public(api_client):
    response = api_client.get("/api/health/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "ok"
    assert response.data["database"] == "ok"
    assert response.data["service"] == "pet-insurance-backend"


@pytest.mark.django_db
def test_schema_and_docs_are_public(api_client):
    schema_response = api_client.get("/api/schema/")
    docs_response = api_client.get("/api/docs/")

    assert schema_response.status_code == status.HTTP_200_OK
    assert docs_response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_can_obtain_and_refresh_tokens(api_client, customer):
    token_response = api_client.post(
        "/api/token/",
        {"email": customer.email, "password": "password123"},
        format="json",
    )

    assert token_response.status_code == status.HTTP_200_OK
    assert "access" in token_response.data
    assert "refresh" in token_response.data

    refresh_response = api_client.post(
        "/api/token/refresh/",
        {"refresh": token_response.data["refresh"]},
        format="json",
    )

    assert refresh_response.status_code == status.HTTP_200_OK
    assert "access" in refresh_response.data
