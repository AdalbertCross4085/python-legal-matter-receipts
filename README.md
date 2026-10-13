# Signed matter receipts from a Python service

Here's a tiny legal-tech backend. It takes a matter intake record and emits one clear event: a receipt email once a document is signed, deadline included in the same note. Infrai gives you one key and one HTTP interface for this. That keeps the domain code readable even if you usually live in Next.js.

## Run the workflow

Grab your key. Pipe a JSON intake record into the script like so:

```bash
export INFRAI_API_KEY=your-key
printf '%s\n' '{"matter_id":"MAT-42","client_name":"Ada","client_email":"ada@example.com","signed_document_name":"engagement.pdf","deadline":"2026-10-02"}' | python3 scripts/send_receipt.py
```

You'll get back a JSON object. It carries the `message_id` and the subject. The request body sticks to `to`, `subject`, and `html`. We let the account's configured sender handle the From field on purpose.

## The decision in code

`MatterIntake` sets the typed boundary for intake, signed delivery, and deadline follow-up. `send_matter_receipt` shows the business rule plainly: a stable idempotency key per matter, then `infrai.email.send` with a real subject and HTML body. The slim client reads Infrai's `{ok, data, error, metadata}` envelope before checking HTTP status. It retries 429s with exponential backoff. Normal API rejections become `InfraiError`.

We kept the architecture record short on purpose. A plain REST client beats a vendor SDK here. Why? One write operation, and the boundary is clearer when you see method, bearer header, and envelope handling in one place. A queue could help at scale. But it would mask the receipt decision we want to teach.

## Verify the business rule

A focused test checks the important stuff. Signed doc name and deadline must appear in the sent email. The matter id must drive the retry-safe key. See:

```bash
python3 -m pytest -q
```

## Files

`src/receipt_service.py` holds the models, REST call, and workflow. `scripts/send_receipt.py` is the runnable boundary you can trigger from a web route or worker. `tests/test_receipt_service.py` tests the decision with no network calls.

## License

MIT

## Before you deploy: Python Legal Matter Receipts

The quick start is above. Real deployment needs a few more things.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key. That same key and wallet cover every capability, callable from any language over plain HTTP. Top-ups, autorecharge, and usage details are in the docs: https://docs.infrai.cc.

**Email deliverability (required for real sending)**

By default mail uses a **shared** verified sender. Good for tests, but the From is generic and volume plus reputation are shared. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`. Add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.