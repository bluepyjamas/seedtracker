# seeds/admin.py
from django.contrib import admin
from .models import SeedBatch, BatchPhoto, OutgoingTransaction, RECOMMEND_WINDOW_DAYS
from django.utils import timezone

@admin.register(SeedBatch)
class SeedBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "seed_name", "weight_grams", "sell_by_date", "recommended_to_process")
    list_filter = ("sell_by_date",)
    search_fields = ("batch_number", "seed_name")


@admin.register(BatchPhoto)
class BatchPhotoAdmin(admin.ModelAdmin):
    list_display = ("batch", "uploaded_at")
    list_filter = ("uploaded_at", "batch")


@admin.register(OutgoingTransaction)
class OutgoingTransactionAdmin(admin.ModelAdmin):
    list_display = ("batch", "type", "quantity_grams", "date")
    list_filter = ("type", "date")
    search_fields = ("batch__batch_number", "batch__seed_name")
