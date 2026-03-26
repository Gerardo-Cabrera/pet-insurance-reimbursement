from datetime import date
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.pets.models import Pet
from apps.users.models import User


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.CLAIMS_PROCESSING_MODE = "sync"
    settings.CLAIMS_PROCESSING_DELAY_SECONDS = 0


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        email="customer@example.com",
        password="password123",
        first_name="Ada",
    )


@pytest.fixture
def other_customer(db):
    return User.objects.create_user(
        email="other@example.com",
        password="password123",
        first_name="Linus",
    )


@pytest.fixture
def support_user(db):
    return User.objects.create_user(
        email="support@example.com",
        password="password123",
        role=User.Role.SUPPORT,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="password123",
    )


@pytest.fixture
def customer_pet(db, customer):
    return Pet.objects.create(
        owner=customer,
        name="Milo",
        species=Pet.Species.DOG,
        birth_date=date(2020, 1, 1),
        coverage_start=date(2026, 1, 1),
    )


@pytest.fixture
def other_pet(db, other_customer):
    return Pet.objects.create(
        owner=other_customer,
        name="Nina",
        species=Pet.Species.CAT,
        birth_date=date(2021, 5, 4),
        coverage_start=date(2026, 1, 1),
    )


@pytest.fixture
def invoice_file():
    return SimpleUploadedFile(
        "invoice.pdf",
        b"fake-pdf-content",
        content_type="application/pdf",
    )


@pytest.fixture
def claim_payload(customer_pet, invoice_file):
    return {
        "pet": customer_pet.id,
        "invoice": invoice_file,
        "invoice_date": "2026-02-10",
        "date_of_event": "2026-02-09",
        "amount": "129.90",
    }
