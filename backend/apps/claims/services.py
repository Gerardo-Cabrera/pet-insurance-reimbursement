import hashlib
import time
from threading import Thread

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.users.models import User

from .models import Claim


def calculate_file_hash(uploaded_file):
    uploaded_file.seek(0)
    digest = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


def collect_coverage_errors(pet, invoice_date, date_of_event):
    errors = []
    if invoice_date < pet.coverage_start or invoice_date > pet.coverage_end:
        errors.append("Invoice date must fall within the pet coverage period.")
    if date_of_event < pet.coverage_start or date_of_event > pet.coverage_end:
        errors.append("Event date must fall within the pet coverage period.")
    return errors


def process_claim(claim_id):
    with transaction.atomic():
        claim = (
            Claim.objects.select_for_update()
            .select_related("pet", "owner")
            .get(pk=claim_id)
        )

        if claim.status != Claim.Status.PROCESSING:
            return claim

        errors = collect_coverage_errors(
            claim.pet,
            claim.invoice_date,
            claim.date_of_event,
        )

        if errors:
            claim.status = Claim.Status.REJECTED
            claim.review_notes = " ".join(errors)
            claim.processing_summary = (
                "Automatic validation failed during claim processing."
            )
        else:
            claim.status = Claim.Status.IN_REVIEW
            claim.processing_summary = (
                "Invoice metadata was simulated and coverage rules were validated."
            )

        claim.save(
            update_fields=["status", "review_notes", "processing_summary", "updated_at"]
        )
        return claim


def _process_claim_with_delay(claim_id):
    delay = max(float(settings.CLAIMS_PROCESSING_DELAY_SECONDS), 0)
    if delay:
        time.sleep(delay)
    process_claim(claim_id)


def dispatch_claim_processing(claim_id):
    mode = settings.CLAIMS_PROCESSING_MODE.lower()

    if mode == "celery":
        from .tasks import process_claim_task

        process_claim_task.delay(claim_id)
        return

    if mode == "thread":
        worker = Thread(target=_process_claim_with_delay, args=(claim_id,), daemon=True)
        worker.start()
        return

    process_claim(claim_id)


def approve_claim(claim, reviewer, notes=""):
    if reviewer.role not in {User.Role.SUPPORT, User.Role.ADMIN}:
        raise ValueError("Only support or admin users can approve claims.")
    if claim.status != Claim.Status.IN_REVIEW:
        raise ValueError("Only claims in review can be approved.")

    claim.status = Claim.Status.APPROVED
    claim.review_notes = notes
    claim.reviewed_by = reviewer
    claim.reviewed_at = timezone.now()
    claim.save(
        update_fields=[
            "status",
            "review_notes",
            "reviewed_by",
            "reviewed_at",
            "updated_at",
        ]
    )
    return claim


def reject_claim(claim, reviewer, notes):
    if reviewer.role not in {User.Role.SUPPORT, User.Role.ADMIN}:
        raise ValueError("Only support or admin users can reject claims.")
    if claim.status != Claim.Status.IN_REVIEW:
        raise ValueError("Only claims in review can be rejected.")
    if not notes or not notes.strip():
        raise ValueError("Rejection notes are required.")

    claim.status = Claim.Status.REJECTED
    claim.review_notes = notes.strip()
    claim.reviewed_by = reviewer
    claim.reviewed_at = timezone.now()
    claim.save(
        update_fields=[
            "status",
            "review_notes",
            "reviewed_by",
            "reviewed_at",
            "updated_at",
        ]
    )
    return claim
