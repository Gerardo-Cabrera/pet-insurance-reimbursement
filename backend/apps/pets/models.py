from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Pet(models.Model):
    class Species(models.TextChoices):
        DOG = "DOG", "Dog"
        CAT = "CAT", "Cat"
        OTHER = "OTHER", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pets",
    )
    name = models.CharField(max_length=120)
    species = models.CharField(max_length=20, choices=Species.choices)
    birth_date = models.DateField()
    coverage_start = models.DateField()
    coverage_end = models.DateField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if self.birth_date and self.coverage_start and self.birth_date > self.coverage_start:
            raise ValidationError("Birth date cannot be after the coverage start date.")

    def save(self, *args, **kwargs):
        if self.coverage_start:
            self.coverage_end = self.coverage_start + timedelta(days=365)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.owner.email})"
