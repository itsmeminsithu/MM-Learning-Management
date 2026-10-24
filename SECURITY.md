# Security

Report issues privately at https://minsithu.org/contact/. Do not post credentials, student details or payment receipts in public issues.

Included controls: Django password hashing and session authentication, CSRF protection on state changes, server-side enrollment/instructor/receipt ownership checks, escaped lesson text, restricted video embed hosts, private receipt downloads, signed card webhooks, price snapshots and idempotent fulfillment.

The owner account can manage all content and payments. Staff accounts can use the instructor studio for their own courses. Creating a learner account never grants staff privileges. The sample author has no usable password.

Read DEPLOYMENT.md before hosting publicly. No software can guarantee security; the release has not received an independent security audit. Back up private data securely and keep dependencies updated.
