# Adorn by SOC Project Rules

## Project
- This is a Django 5.2 e-commerce website for Adorn by SOC.
- Main apps: core, catalog, cart, orders, payments, dashboard.
- Current production branch is main.
- Git remote is origin.

## Safety
- Never commit or expose:
  - .env
  - Django SECRET_KEY
  - Stripe secret keys
  - Stripe webhook secret
  - database passwords
  - customer personal data
  - db.sqlite3
  - media/
  - staticfiles/
  - venv/
  - backup ZIP files
- Never use git push --force.
- Never run git reset --hard, git clean -fd, or destructive file deletion without explicit approval.
- Do not modify unrelated files.

## Editing workflow
Before making changes:
1. Inspect all related files.
2. Explain the planned changes briefly.
3. Preserve existing functionality and design unless explicitly asked otherwise.

After every requested change:
1. Run:
   python manage.py check
2. Run relevant tests.
3. Review:
   git status
   git diff
4. Verify no secrets or sensitive files are included.
5. If checks pass, commit with a clear descriptive commit message.
6. Push to origin main.
7. Report:
   - files changed
   - checks run
   - commit hash
   - push status

If checks fail:
- Do not push broken code.
- Fix the issue first or explain clearly what failed.

## Project-specific notes
- Database is currently SQLite.
- MySQL dependencies exist but MySQL is not yet configured in settings.py.
- Stripe payments use INR and environment variables.
- media/ and staticfiles/ must remain gitignored.
