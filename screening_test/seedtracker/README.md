# Seed Tracker

Minimal Django app to track seed batches, support quarantine, and provide an auditor view with CSV export.

## Tech
- Python 3.10+
- Django 4.x+
- SQLite

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install "Django>=4.2"
python manage.py migrate
python manage.py runserver
