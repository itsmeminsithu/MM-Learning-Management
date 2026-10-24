# Validation for this package

Validated locally on Linux with Python 3.12, Django 5.2.18, Stripe SDK 14.4.1 and Pillow 12.3.0.

- Django system checks and migration consistency.
- 17 automated regression tests covering public/student/editor page rendering, enrollment, paid-course access, course boundaries, quiz validation, certificate eligibility/ownership, instructor isolation, CSRF, signup privileges, embed allowlisting and repeatable seeding.
- Payment tests cover server-side prices, disabled methods, invalid receipt uploads, private receipts, manual approval/rejection, signed webhook amount/signature matching, duplicate events, return-URL spoofing and private QR responses.
- Clean extracted-package database migration and sample-data setup.

No live merchant transactions were executed. Hosted checkout creation is mocked in its unit test; webhook tests use locally signed test payloads. macOS and Windows launchers and the CI matrix are included but have not been executed on those operating systems here. Browser visual and accessibility audits have not been completed; route/template responses were tested using Django's test client.

Run the suite yourself:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
