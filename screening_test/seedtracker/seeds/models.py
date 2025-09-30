
from django.conf import settings
from django.db import models
from django.db.models import F
from django.core.exceptions import ValidationError
from django.utils import timezone


RECOMMEND_WINDOW_DAYS = getattr(settings, "RECOMMEND_WINDOW_DAYS", 30)


class SeedBatch(models.Model):
    seed_name = models.CharField(max_length=200, default="Unknown")
    batch_number = models.CharField(max_length=100, unique=True)
    weight_grams = models.DecimalField(max_digits=12, decimal_places=2)
    sell_by_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sell_by_date", "batch_number"]

    def __str__(self):
        return f"{self.seed_name} — {self.batch_number}"

    @property
    def recommended_to_process(self) -> bool:
        today = timezone.localdate()
        return (
            self.sell_by_date is not None
            and self.sell_by_date <= (today + timezone.timedelta(days=RECOMMEND_WINDOW_DAYS))
        )


class BatchPhoto(models.Model):
    batch = models.ForeignKey(SeedBatch, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="batch_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.batch.batch_number} @ {self.uploaded_at:%Y-%m-%d %H:%M}"


class OutgoingTransaction(models.Model):
    TYPE_CHARITY = "charity"
    TYPE_PRINTER_ERROR = "printer_error"
    TYPE_MACHINE_ERROR = "machine_error"
    TYPE_DISPOSAL = "disposal"
    TYPE_CHOICES = [
        (TYPE_CHARITY, "Charity"),
        (TYPE_PRINTER_ERROR, "Printer error"),
        (TYPE_MACHINE_ERROR, "Machine error"),
        (TYPE_DISPOSAL, "Disposal"),
    ]

    batch = models.ForeignKey(
        SeedBatch, on_delete=models.PROTECT, related_name="outgoing_transactions"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity_grams = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def clean(self):
   
        if self.quantity_grams is None or self.quantity_grams <= 0:
            raise ValidationError(
                {"quantity_grams": "Quantity must be a positive amount in grams."}
            )

     
        if (
            self.batch
            and self.batch.weight_grams is not None
            and self.quantity_grams > self.batch.weight_grams
        ):
            raise ValidationError(
                {
                    "quantity_grams": "Quantity exceeds current batch weight. "
                    "This would make inventory negative."
                }
            )
