# MM Learning Management

An original, self-hosted learning platform for courses, progress tracking, quizzes and certificates, with Myanmar transfer-payment workflows and optional hosted card checkout.

**Created by Min SiThu ([itsmeminsithu](https://github.com/itsmeminsithu))**  
[minsithu.org](https://minsithu.org/) · [Contact](https://minsithu.org/contact/) · MIT License

**Live preview — real app, in GitHub only:** [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/itsmeminsithu/MM-Learning-Management) — this launches the real Django app in GitHub Codespaces. No external host, no static mock. See the Codespaces steps below.

## What works in this release

- Responsive course catalog, keyword search and category filters.
- Student registration, sign-in, personal dashboard and enrollment.
- Plain-text lessons with optional approved YouTube/Vimeo embeds.
- Persistent lesson progress, server-graded quizzes and retry history.
- Completion certificates with printable layouts; save to PDF using your browser.
- Instructor studio: create courses, edit lessons/questions, set prices and publish.
- Owner administration for users, instructor access and payment configuration.
- KPay, WavePay, AYA Bank, KBZ Bank and MMQR: configure merchant instructions/QR, submit a private receipt, review and approve enrollment.
- Optional Stripe hosted card checkout with signed webhook verification. Visa, Mastercard and UnionPay depend on merchant eligibility and provider availability.
- SQLite persistence, database migrations and regression tests.
- Three original short sample courses. These demonstrate workflows; replace them with your own curriculum.

This is a runnable foundation, not a complete enterprise LMS. Live classrooms, SCORM, organizations, subscriptions, instructor commissions/payouts, refunds, accounting, chat, assignments, coupons and full Burmese interface localization are **not implemented**. See [ROADMAP.md](ROADMAP.md). Burmese course text is supported through Unicode. No third-party LMS code, templates, artwork or course content is bundled.

## Live preview in GitHub Codespaces

GitHub Pages cannot run this Django backend, so there is no always-on public app link from GitHub alone. Codespaces is the GitHub-only way to run the real app live:

1. Click **Open in GitHub Codespaces** above (or open https://codespaces.new/itsmeminsithu/MM-Learning-Management), choose a 2-core machine, and wait for setup. Setup installs the dependencies, runs migrations and checks the project.
2. In the Codespace terminal, run:

```bash
python3 start.py
```

On first run, create your owner username and password when prompted. There is **no default password**.
3. When port **8000** forwards, open it from the preview prompt or the Ports tab. That forwarded page is the real app, not a mock.
4. Sign in with your owner account, open **Instructor studio** to try the sample courses, or register a separate student account to test enrollment, quizzes and certificates.
5. Stop the Codespace when you are done, to save your free quota. Data in a Codespace lives in that Codespace only — it is a demo, not a shared production academy.

## Run on Mac

Install Python **3.11 or newer** from [python.org](https://www.python.org/downloads/). Python 3.13 is suitable. Then:

```bash
git clone https://github.com/itsmeminsithu/MM-Learning-Management.git
cd MM-Learning-Management
python3 start.py
```

The launcher creates `.venv`, installs dependencies, migrates the database and adds sample courses. On first run, create your owner username and password when prompted. There is **no default password**. Password input is hidden while typing.

Open **http://127.0.0.1:8000**. Press **Control+C** in Terminal to stop. Start again with the same command; your data persists.

You can also run `bash Start-MM-Learning.command` from the project folder. If double-click launching is blocked, use the Terminal command above. Do not disable macOS security settings.

Windows: install Python 3.11+, then double-click `Start-MM-Learning.bat` or run `py -3 start.py`. Linux: `python3 start.py`.

Internet is required for the first dependency installation, optional web fonts and embedded videos. Core reading and progress work locally after installation. The app binds to your own computer only.

## Use the platform

1. Sign in with your owner account. Open **Instructor studio** to edit the sample courses or create a new course.
2. Add lessons and optionally quiz questions. Set a price of `0` for a free course. Publish when ready.
3. To add an instructor, create a user at `/admin/`, set **Staff status**, and leave **Superuser status** off. They can edit only their own courses through the studio. Do not grant unrelated admin permissions.
4. Register a separate student account to test enrollment, completion, quizzes and certificates.
5. For paid MMK courses, configure real payment details at `/admin/learning/paymentmethod/`. Enable only the methods you actually accept.
6. Students submit receipts under **Purchases**. The owner verifies funds in the merchant account and approves under **Payments**.

Sample courses belong to an inactive `sample_author` account with no usable password. The owner can edit them and reassign instructors through the admin panel. Seeding again does not overwrite existing courses or payment settings.

## Payments

Manual payment options work once you enter your real merchant details. They are **not direct banking API integrations**. MMQR displays a merchant-supplied QR image; it does not generate dynamic MMQR payloads or automatically confirm transfers.

Cards use an optional Stripe adapter, disabled until keys and a webhook are configured. This is not a claim that a Myanmar-based business is eligible for Stripe. Use an approved merchant account in a supported jurisdiction or implement a locally approved gateway adapter. The current adapter offers USD/THB courses only; MMK courses use manual payment methods. No currency conversion is performed.

Read [PAYMENTS.md](PAYMENTS.md) before accepting money. Live banking/card transactions were not executed as part of package testing.

## Developer setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

On Windows, activate using `.venv\Scripts\activate` instead.

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Stack: Python, Django 5.2, SQLite, server-rendered HTML, CSS, minimal JavaScript, Pillow and the Stripe Python SDK. Dependencies keep their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).

## Data and configuration

Local database, generated development secret and private uploads live in `.local-data/`. Back up this directory securely. Do not publish it. Secrets are read from environment variables; `.env.example` is documentation and is **not automatically loaded**.

Main source files:

- `learning/models.py`: courses, learning records and orders.
- `learning/views.py`: enrollment, assessments and instructor tools.
- `learning/payments.py`: hosted checkout, private receipts and review.
- `learning/tests.py`: authorization and workflow tests.
- `templates/` and `static/`: original interface.
- `config/settings.py`: environment configuration.

## Troubleshooting

- `python3: command not found`: install Python, reopen Terminal and check `python3 --version`.
- Dependency install error: confirm internet access, then rerun `python3 start.py`.
- Port already in use: stop the earlier server, or use `.venv/bin/python manage.py runserver 127.0.0.1:8001`.
- Forgot owner password: `.venv/bin/python manage.py changepassword YOUR_USERNAME`.
- Payment options missing: enable a method with the same currency as the course. No fake payment accounts are included.
- Paid course still locked: uploading a receipt does not grant access. An owner must verify and approve it.

## Deploy

GitHub Pages cannot run this Django backend. The launcher uses a development server; read [DEPLOYMENT.md](DEPLOYMENT.md) before public hosting.

Copyright © 2026 Min SiThu (devminsithu). Original project code is released under the [MIT License](LICENSE).
