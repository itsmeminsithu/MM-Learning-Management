# Payment configuration

## Manual Myanmar payments

Sign in as the owner and visit `/admin/learning/paymentmethod/`. The seed command adds disabled entries for KPay (KBZPay), WavePay, AYA Bank, KBZ Bank and MMQR.

For each method you accept:

1. Enter the real account name, account number and clear transfer instructions.
2. Optionally upload your real merchant QR image. Ensure the QR recipient matches the displayed account.
3. Set the accepted currency, normally MMK, and enable the method.
4. Publish a course with a positive price in that currency.
5. Test with a separate student. Checkout creates an order with a server-side price snapshot. A PNG/JPEG receipt up to 2 MB and a transaction reference can be submitted once.
6. Review the receipt at `/payment-reviews/`. Independently verify the amount, currency, recipient and transaction ID in your bank/wallet account. Check that the reference has not already been used for a different order. Approve only when funds are actually received.

Receipt images are private, available only to the student and superuser. Upload storage must never be served as a public media directory. Approval records the reviewing owner and creates enrollment in the same database transaction. Rejection does not grant access; the learner should contact you before paying again. Duplicate review requests cannot grant duplicate enrollment.

MMQR is merchant-supplied static QR display with manual reconciliation. There is no bank API, settlement confirmation, automatic duplicate-bank-reference detection, refund or dispute service. Retain financial records according to your operating requirements and verify every manual payment.

## Optional hosted cards

The included adapter is Stripe Checkout. Before using it, verify your business is eligible at https://stripe.com/global and confirm supported brands/currencies at https://docs.stripe.com/payments/cards. UnionPay availability is conditional. This package does not provide a merchant account or circumvent onboarding requirements.

The adapter accepts USD or THB course prices. It does not convert MMK amounts. Use test mode first:

```bash
export STRIPE_SECRET_KEY='YOUR_STRIPE_TEST_SECRET_KEY'
export STRIPE_WEBHOOK_SECRET='YOUR_TEST_WEBHOOK_SIGNING_SECRET'
python3 start.py
```

These are placeholders, not credentials. Do not commit keys. For local testing, use the official Stripe CLI to forward events to:

```
http://127.0.0.1:8000/payments/stripe/webhook/
```

Use the signing secret issued for that forwarding session. On a hosted HTTPS installation, register the same path as an event destination and configure its own signing secret. Subscribe to `checkout.session.completed` and `checkout.session.async_payment_succeeded`. Follow https://docs.stripe.com/webhooks for CLI setup and test payment details.

A successful browser redirect never fulfills an order. The webhook verifies the signature, order ID, Checkout Session ID, currency, exact amount, mode and test/live context. Only a paid session grants enrollment. Replayed paid events are idempotent. A webhook arriving before the Checkout Session ID is saved receives a retryable error; configure provider retries and monitor failed deliveries.

There is no automatic card retry/resume UI for abandoned sessions. Contact the owner before creating another order if funds might already have been charged. Review provider records for duplicates. Refunds and disputes must be handled in the provider dashboard and enrollment access adjusted operationally; automatic refund/revocation synchronization is not implemented.

For another gateway: add a separate provider adapter with signed callbacks, exact amount/currency checks and idempotent fulfillment. Never accept an unsigned `paid=true` parameter or collect raw card details in this app.

References: https://docs.stripe.com/api/checkout/sessions/create and https://docs.stripe.com/webhooks.
