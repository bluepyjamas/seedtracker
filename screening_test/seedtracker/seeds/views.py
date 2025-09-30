
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import BooleanField, Case, Value, When
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

import csv
from decimal import Decimal

from .models import SeedBatch, BatchPhoto, OutgoingTransaction, RECOMMEND_WINDOW_DAYS
from .forms import SeedBatchForm, OutgoingTransactionForm, BatchPhotoMultiUploadForm
from .permissions import user_is_staff_role, user_is_auditor

# ----- SeedBatch list with Recommended flag, filter, and sort -----

@login_required
def seedbatch_list(request):
    qs = SeedBatch.objects.all()

   
    today = timezone.localdate()
    cutoff = today + timezone.timedelta(days=RECOMMEND_WINDOW_DAYS)
    qs = qs.annotate(
        recommended=Case(
            When(sell_by_date__lte=cutoff, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )

    # Filters
    recommended_filter = request.GET.get("recommended")
    if recommended_filter in {"yes", "no"}:
        qs = qs.filter(recommended=(recommended_filter == "yes"))

    # Search (optional nice-to-have)
    q = request.GET.get("q")
    if q:
        qs = qs.filter(models.Q(seed_name__icontains=q) | models.Q(batch_number__icontains=q))

    # Sort by recommended if requested
    sort = request.GET.get("sort")
    if sort == "recommended":
        qs = qs.order_by("-recommended", "sell_by_date")

    context = {
        "batches": qs,
        "recommended_filter": recommended_filter,
        "sort": sort,
        "q": q or "",
        "recommend_window_days": RECOMMEND_WINDOW_DAYS,
    }
    return render(request, "seeds/seedbatch_list.html", context)

# ----- SeedBatch CRUD -----

@login_required
@user_passes_test(lambda u: user_is_staff_role(u) or user_is_auditor(u))
def seedbatch_detail(request, pk):
    batch = get_object_or_404(SeedBatch, pk=pk)
    can_edit = user_is_staff_role(request.user)
    return render(request, "seeds/seedbatch_detail.html", {"batch": batch, "can_edit": can_edit})

@login_required
@user_passes_test(user_is_staff_role)
def seedbatch_create(request):
    if request.method == "POST":
        form = SeedBatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, "Batch created.")
            return redirect("seeds:seedbatch_detail", pk=batch.pk)
    else:
        form = SeedBatchForm()
    return render(request, "seeds/seedbatch_form.html", {"form": form})

@login_required
@user_passes_test(user_is_staff_role)
def seedbatch_update(request, pk):
    batch = get_object_or_404(SeedBatch, pk=pk)
    if request.method == "POST":
        form = SeedBatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, "Batch updated.")
            return redirect("seeds:seedbatch_detail", pk=batch.pk)
    else:
        form = SeedBatchForm(instance=batch)
    return render(request, "seeds/seedbatch_form.html", {"form": form, "batch": batch})

@login_required
@user_passes_test(user_is_staff_role)
def seedbatch_delete(request, pk):
    batch = get_object_or_404(SeedBatch, pk=pk)
    if request.method == "POST":
        batch.delete()
        messages.success(request, "Batch deleted.")
        return redirect("seeds:seedbatch_list")
    return render(request, "seeds/confirm_delete.html", {"batch": batch})

# ----- Batch photo upload (multi) -----

@login_required
@user_passes_test(user_is_staff_role)
def batchphoto_upload(request):
    if request.method == "POST":
        form = BatchPhotoMultiUploadForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.cleaned_data["batch"]
            images = request.FILES.getlist("images")
            for img in images:
                BatchPhoto.objects.create(batch=batch, image=img)
            messages.success(request, f"Uploaded {len(images)} photo(s) to batch {batch.batch_number}.")
            return redirect("seeds:seedbatch_detail", pk=batch.pk)
    else:
        form = BatchPhotoMultiUploadForm()
    return render(request, "seeds/batchphoto_upload.html", {"form": form})


@login_required
@user_passes_test(user_is_staff_role)
def outgoing_create(request, batch_pk=None):
    initial = {}
    if batch_pk:
        initial["batch"] = get_object_or_404(SeedBatch, pk=batch_pk)
    if request.method == "POST":
        form = OutgoingTransactionForm(request.POST)
        if form.is_valid():
            batch = form.cleaned_data["batch"]
            qty = form.cleaned_data["quantity_grams"]
            try:
                with transaction.atomic():
                    # Lock the batch row
                    locked_batch = SeedBatch.objects.select_for_update().get(pk=batch.pk)
                    if qty > locked_batch.weight_grams:
                        form.add_error("quantity_grams", "Quantity exceeds current batch weight (cannot go negative).")
                        raise ValueError("Invalid quantity")
                    # Create transaction
                    tx = form.save()
                    # Atomic decrement
                    SeedBatch.objects.filter(pk=batch.pk).update(weight_grams=F("weight_grams") - qty)
                messages.success(request, "Outgoing transaction recorded and inventory updated.")
                return redirect("seeds:seedbatch_detail", pk=batch.pk)
            except ValueError:
                # Form already has errors
                pass
    else:
        form = OutgoingTransactionForm(initial=initial)
    return render(request, "seeds/outgoing_form.html", {"form": form})

# ----- Auditor CSV exports -----

@login_required
@user_passes_test(user_is_auditor)
def export_batches_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="seed_batches.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "id", "batch_number", "seed_name", "weight_grams", "sell_by_date",
        "recommended_to_process", "created_at"
    ])
    for b in SeedBatch.objects.all().order_by("sell_by_date", "batch_number"):
        writer.writerow([
            b.id, b.batch_number, b.seed_name, f"{b.weight_grams:.2f}",
            b.sell_by_date, "Yes" if b.recommended_to_process else "No", b.created_at
        ])
    return response

@login_required
@user_passes_test(user_is_auditor)
def export_outgoing_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="outgoing_transactions.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "id", "batch_id", "batch_number", "seed_name", "type", "quantity_grams", "notes", "date"
    ])
    qs = OutgoingTransaction.objects.select_related("batch").all().order_by("-date", "id")
    for t in qs:
        writer.writerow([
            t.id, t.batch_id, t.batch.batch_number, t.batch.seed_name,
            t.type, f"{t.quantity_grams:.2f}", t.notes, t.date
        ])
    return response

# ----- Printable Seed Tag (PDF) -----

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

@login_required
@user_passes_test(lambda u: user_is_staff_role(u) or user_is_auditor(u))
def print_seed_tag_pdf(request, pk):
    batch = get_object_or_404(SeedBatch, pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="seed_tag_{batch.batch_number}.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Margins
    left = 20 * mm
    top = height - 20 * mm
    line_gap = 10 * mm

    # Seed Name (largest)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(left, top, batch.seed_name)

    # Other fields
    c.setFont("Helvetica", 14)
    y = top - line_gap
    c.drawString(left, y, f"Batch Number: {batch.batch_number}")
    y -= line_gap
    c.drawString(left, y, f"Weight (current): {batch.weight_grams:.2f} g")
    y -= line_gap
    c.drawString(left, y, f"Sell By Date: {batch.sell_by_date:%Y-%m-%d}")
    y -= line_gap
    c.drawString(left, y, f"Recommended to Process: {'Yes' if batch.recommended_to_process else 'No'}")

    c.showPage()
    c.save()
    return response
