from django.contrib import admin

from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "pet", "owner", "status", "amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__email", "pet__name", "invoice_hash")
