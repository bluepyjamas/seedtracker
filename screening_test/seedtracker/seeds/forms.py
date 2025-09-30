# seeds/forms.py
from django import forms
from .models import SeedBatch, BatchPhoto, OutgoingTransaction


class SeedBatchForm(forms.ModelForm):
    class Meta:
        model = SeedBatch
        fields = ["seed_name", "batch_number", "weight_grams", "sell_by_date"]


class OutgoingTransactionForm(forms.ModelForm):
    class Meta:
        model = OutgoingTransaction
        fields = ["batch", "type", "quantity_grams", "notes"]

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get("quantity_grams")
        batch = cleaned.get("batch")
        if qty is not None and qty <= 0:
            self.add_error("quantity_grams", "Quantity must be positive.")
        if batch and qty and batch.weight_grams is not None and qty > batch.weight_grams:
            self.add_error("quantity_grams", "Quantity exceeds current batch weight.")
        return cleaned


# --- Custom widget/field for multiple file uploads ---
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class BatchPhotoMultiUploadForm(forms.Form):
    batch = forms.ModelChoiceField(queryset=SeedBatch.objects.all())
    images = MultipleFileField(
        label="Select images",
        required=True,
        help_text="You can select multiple photos (hold Ctrl/Cmd)."
    )

    def clean_images(self):
        files = self.files.getlist("images")
        if not files:
            raise forms.ValidationError("Please select at least one image.")
        # Optional: basic validation
        for f in files:
            if f.size > 10 * 1024 * 1024:
                raise forms.ValidationError(f"{f.name}: File too large (max 10MB).")
        return files
