# seeds/urls.py
from django.urls import path
from django.shortcuts import render
from . import views

app_name = "seeds"

urlpatterns = [
    # Seed batch CRUD
    path("", views.seedbatch_list, name="seedbatch_list"),
    path("batch/<int:pk>/", views.seedbatch_detail, name="seedbatch_detail"),
    path("batch/new/", views.seedbatch_create, name="seedbatch_create"),
    path("batch/<int:pk>/edit/", views.seedbatch_update, name="seedbatch_update"),
    path("batch/<int:pk>/delete/", views.seedbatch_delete, name="seedbatch_delete"),

    # Auditor exports page (simple template)
    path(
        "auditor/exports/",
        lambda r: render(r, "seeds/auditor_exports.html"),
        name="auditor_exports",
    ),

    # Batch photos
    path("photos/upload/", views.batchphoto_upload, name="batchphoto_upload"),

    # Outgoing transactions
    path("outgoing/new/", views.outgoing_create, name="outgoing_create"),
    path("outgoing/new/<int:batch_pk>/", views.outgoing_create, name="outgoing_create_for_batch"),

    # CSV exports
    path("auditor/export/batches.csv", views.export_batches_csv, name="export_batches_csv"),
    path("auditor/export/outgoing.csv", views.export_outgoing_csv, name="export_outgoing_csv"),

    # PDF seed tag
    path("batch/<int:pk>/print-tag.pdf", views.print_seed_tag_pdf, name="print_seed_tag_pdf"),
]
