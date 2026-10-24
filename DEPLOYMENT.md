# Public hosting

The included launcher is for local development. This package has not been load-tested or independently security-audited. Do not expose Django's `runserver` to the Internet.

Before public operation:

1. Use a maintained Python runtime and a production WSGI/ASGI server behind an HTTPS reverse proxy. Install and configure that server separately.
2. Set `DJANGO_DEBUG=0`, a high-entropy `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS` to your actual hostnames. Keep secrets outside the repository. Settings enable secure cookies and HTTPS redirects in production. Configure trusted proxy headers only if your own proxy strips incoming spoofed headers.
3. Run migrations and `python manage.py collectstatic`. Serve `staticfiles/` separately. Never expose `.local-data/` or private payment uploads as static/media files.
4. Configure request body limits (for example 3 MB), authentication/registration rate limits, request timeouts and abuse monitoring at the proxy/application boundary. A distributed login throttle, email verification, email password reset and MFA are not included.
5. Review database choice before concurrent production workloads. SQLite is intended for this local starter; migrate to PostgreSQL with a separately configured database driver/settings and test payment concurrency before scaling. Take encrypted backups and test restores.
6. Use your own course content and policies. Configure merchant accounts, test signed webhooks and receipt review, and verify all payment flows in provider test mode before live payments.
7. Configure operational logging, alerts, receipt retention, support and refunds. Keep secrets/card data out of logs. Add privacy/terms pages appropriate to your deployment; they are not included.
8. Run `python manage.py check --deploy` with your actual production settings. Resolve warnings and test HTTPS, cookies, static assets, private downloads and webhooks.

No public deployment, DNS, hosting account or live merchant setup is included in this ZIP. The GitHub Actions workflow is provided; its cross-platform runs have not been executed until you push to GitHub.

Django deployment checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
