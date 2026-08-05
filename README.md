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

## Frontend: React islands (motion-primitives)

Most of the site is plain Django templates + hand-written CSS. React is used
only where a page opts in, so no other page pays for the bundle.

Add a component:

```
npx motion-primitives@latest add <component>   # lands in components/motion-primitives/
```

Register it in `frontend/main.tsx`, then rebuild:

```
npm run build        # writes static/dist/adorn.js + adorn.css (npm run watch to rebuild on save)
```

Use it in any template — Django renders the div, React renders what goes inside:

```html
{% block extra_css %}<link rel="stylesheet" href="{% static 'dist/adorn.css' %}">{% endblock %}

<div data-react="TextEffect" data-props='{"children": "Adorn by SOC", "per": "char"}'></div>

{% block extra_js %}<script type="module" src="{% static 'dist/adorn.js' %}"></script>{% endblock %}
```

Working reference: `/dev/motion/` (DEBUG only) — `templates/dev/motion.html`.

Notes:
- Tailwind ships **without preflight** (`frontend/tailwind.css`). Preflight would
  reset the site's own CSS. Only theme + utilities are imported.
- `static/dist/` is committed so deploys don't need Node. Rebuild and commit it
  whenever an island changes.
