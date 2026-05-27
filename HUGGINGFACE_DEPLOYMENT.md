# Hugging Face Deployment

This project can run fully inside one Hugging Face Docker Space.

The Docker image builds the Vite frontend, copies it into the Django backend, runs migrations and seed data, then starts Gunicorn on port `7860`.

## Create the Space

1. Go to <https://huggingface.co/spaces>.
2. Click **Create new Space**.
3. Choose:
   - **Space name:** `carbon-tracker`
   - **SDK:** `Docker`
   - **Visibility:** Public or Private
4. Create the Space.

## Push This Repo to the Space

Clone your Space repository:

```bash
git clone https://huggingface.co/spaces/YOUR_HF_USERNAME/carbon-tracker
cd carbon-tracker
```

Copy this project into that folder, then push:

```bash
git add .
git commit -m "Deploy Carbon Tracker to Hugging Face"
git push
```

Hugging Face will build from `Dockerfile`.

## Recommended Secrets

In the Space page, go to:

```text
Settings -> Repository secrets
```

Add:

```text
DJANGO_SECRET_KEY=your-long-random-secret
DJANGO_DEBUG=False
```

The app can run with SQLite by default. For durable production data, add a PostgreSQL URL:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

## Demo Login

The startup command runs `python manage.py seed_data`.

Default demo users:

```text
admin / admin123
analyst / analyst123
```

## Important Storage Note

Without Hugging Face persistent storage or external PostgreSQL, uploaded files and SQLite data can be lost when the Space rebuilds.
