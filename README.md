# MM Learning Management

A self-hosted learning platform: courses, progress tracking, quizzes and certificates. Payments work the way a lot of Myanmar courses take them — KPay, WavePay, AYA, KBZ and MMQR receipts that an owner checks and approves — with optional Stripe card checkout.

**Created by Min SiThu ([itsmeminsithu](https://github.com/itsmeminsithu))**
[minsithu.org](https://minsithu.org/) · [Contact](https://minsithu.org/contact/) · MIT License

**Run the real app in GitHub:** [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/itsmeminsithu/MM-Learning-Management) — this starts the actual Django app in Codespaces. No other host, no static copy. Steps below.

## What works, and what does not

Works in this release:

- Course catalog that fits the screen, with keyword search and category filters.
- Student registration, sign-in, a personal dashboard and enrollment.
- Plain-text lessons, with YouTube/Vimeo embeds when approved.
- Lesson progress that is saved, quizzes graded on the server, and a record of retries.
- Completion certificates with a printable layout. Save to PDF from your browser.
- Instructor studio: create courses, edit lessons and questions, set prices, publish.
- Owner admin for users, instructor access and payment settings.
- KPay, WavePay, AYA Bank, KBZ Bank and MMQR: set your merchant instructions and QR, the student sends a private receipt, you review it and approve the enrollment.
- Optional Stripe hosted card checkout, with signed webhook checks. Visa, Mastercard and UnionPay depend on merchant eligibility and what the provider offers.
- SQLite storage, database migrations and regression tests.
- Three short sample courses I wrote for this package. They show how things work; replace them with your own.

Not built yet: live classrooms, SCORM, organizations, subscriptions, instructor commissions and payouts, refunds, accounting, chat, assignments, coupons and a full Burmese interface. This is a working base, not a finished enterprise LMS. See [ROADMAP.md](ROADMAP.md). Burmese course text works through Unicode. No third-party LMS code, templates, artwork or course content is included.

## Codespaces

GitHub Pages cannot run a Django backend, so GitHub alone gives no always-on public link for this app. Codespaces runs the real app:

1. Click **Open in GitHub Codespaces** above (or open https://codespaces.new/itsmeminsithu/MM-Learning-Management), choose a 2-core machine, and wait for setup. Setup installs the dependencies, runs migrations and checks the project.
2. In the Codespace terminal, run:

```bash
python3 start.py
```

On first run, create your owner username and password when asked. There is **no default password**.
3. When port **8000** forwards, open it from the preview prompt or the Ports tab.
4. Sign in with your owner account, open **Instructor studio** to try the sample courses, or register a separate student account to test enrollment, quizzes and certificates.
5. Stop the Codespace when you finish, to save your free quota. Data in a Codespace lives in that Codespace only. It is a demo, not a shared production school.

## Run it on a Mac

Install Python **3.11 or newer** from [python.org](https://www.python.org/downloads/). Python 3.13 is fine. Then:

```bash
git clone https://github.com/itsmeminsithu/MM-Learning-Management.git
cd MM-Learning-Management
python3 start.py
```

The launcher creates `.venv`, installs dependencies, migrates the database and adds the sample courses. On first run, create your owner username and password when asked. There is **no default password**. Password input is hidden as you type.

Open **http://127.0.0.1:8000**. Press **Control+C** in Terminal to stop. Start again with the same command; your data stays.

You can also run `bash Start-MM-Learning.command` from the project folder. If double-click launching is blocked, use the Terminal command above. Do not turn off macOS security settings.

Windows: install Python 3.11+, then double-click `Start-MM-Learning.bat` or run `py -3 start.py`. Linux: `python3 start.py`.

The first install needs internet, as do optional web fonts and embedded videos. Reading and progress work locally after that. The app only listens on your computer.

## Using it

1. Sign in as the owner. Open **Instructor studio** to edit the sample courses or start a new one.
2. Add lessons and, if you want them, quiz questions. Set a price of `0` for a free course. Publish when it is ready.
3. To add an instructor, create a user at `/admin/`, turn on **Staff status**, and leave **Superuser status** off. Instructors can only edit their own courses in the studio. Do not hand out wider admin access.
4. Register a separate student account and test enrollment, completion, quizzes and certificates yourself.
5. For paid MMK courses, put your real payment details at `/admin/learning/paymentmethod/`. Only turn on methods you actually accept.
6. Students send receipts under **Purchases**. Check the money arrived in your merchant account, then approve under **Payments**.

The sample courses belong to an inactive `sample_author` account with no usable password. The owner can edit them and change their instructor in admin. Seeding again does not overwrite existing courses or payment settings.

## Payments, stated plainly

The manual methods work once you enter your real merchant details. They are **not direct banking API integrations**. MMQR shows a QR image you supply. It does not create dynamic MMQR payloads and it does not confirm a transfer by itself.

Cards go through an optional Stripe adapter, which stays off until you set up keys and a webhook. Nothing here says a Myanmar-based business can get Stripe. Use an approved merchant account in a supported country, or write an adapter for a local gateway. The current adapter only handles USD/THB courses. MMK courses use the manual methods. There is no currency conversion.

Read [PAYMENTS.md](PAYMENTS.md) before you take money through this. No live bank or card transaction was run while this package was tested.

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

On Windows, activate with `.venv\Scripts\activate` instead.

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Stack: Python, Django 5.2, SQLite, server-rendered HTML, CSS, a small amount of JavaScript, Pillow and the Stripe Python SDK. Dependencies keep their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).

## Data and settings

The local database, the generated development secret and private uploads live in `.local-data/`. Back that folder up and keep the backup safe. Do not publish it. Secrets are read from environment variables. `.env.example` documents them and is **not loaded automatically**.

Main source files:

- `learning/models.py` — courses, learning records and orders.
- `learning/views.py` — enrollment, quizzes and instructor tools.
- `learning/payments.py` — hosted checkout, private receipts and review.
- `learning/tests.py` — permission and workflow tests.
- `templates/` and `static/` — the interface.
- `config/settings.py` — environment settings.

## Troubleshooting

- `python3: command not found` — install Python, reopen Terminal and check `python3 --version`.
- Dependency install error — check your internet connection, then run `python3 start.py` again.
- Port already in use — stop the earlier server, or use `.venv/bin/python manage.py runserver 127.0.0.1:8001`.
- Forgot owner password — `.venv/bin/python manage.py changepassword YOUR_USERNAME`.
- Payment options missing — turn on a method in the same currency as the course. No test payment accounts are included.
- Paid course still locked — sending a receipt does not open the course. An owner has to check it and approve it.

## Hosting it

GitHub Pages cannot run this Django backend. The launcher uses a development server. Read [DEPLOYMENT.md](DEPLOYMENT.md) before you put this on a public server.

Copyright © 2026 Min SiThu (devminsithu). Original project code is released under the [MIT License](LICENSE).
