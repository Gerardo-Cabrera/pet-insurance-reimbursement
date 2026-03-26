from celery import shared_task

from .services import process_claim


@shared_task
def process_claim_task(claim_id):
    process_claim(claim_id)
