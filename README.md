# Adorn By Soc (Django + MySQL + Stripe INR)

## Setup (Windows / VS Code)
1) Create venv and install:
   - `python -m venv venv`
   - `venv\Scripts\activate`
   - `pip install -r requirements.txt`

2) Copy `.env.example` to `.env` and fill MySQL + Stripe keys.

3) Create DB in MySQL:
   - `CREATE DATABASE adornbysoc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`

4) Run migrations + create admin:
   - `python manage.py makemigrations`
   - `python manage.py migrate`
   - `python manage.py createsuperuser`

5) Run:
   - `python manage.py runserver`

## Stripe
- PaymentIntent flow is used.
- Webhook endpoint:
  - `/payments/stripe/webhook/`
