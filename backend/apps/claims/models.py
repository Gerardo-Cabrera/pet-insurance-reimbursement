from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Claim(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        PROCESSING = "PROCESSING", "Processing"
        IN_REVIEW = "IN_REVIEW", "In review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="claims",
    )
    pet = models.ForeignKey(
        "pets.Pet",
        on_delete=models.PROTECT,
        related_name="claims",
    )
    invoice = models.FileField(upload_to="claims/invoices/%Y/%m/%d")
    invoice_hash = models.CharField(max_length=64, unique=True)
    invoice_date = models.DateField()
    date_of_event = models.DateField()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    review_notes = models.TextField(blank=True)
    processing_summary = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_claims",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Claim #{self.pk} - {self.status}"
