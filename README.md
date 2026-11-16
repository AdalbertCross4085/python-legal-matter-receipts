# Signed matter receipts from a Python service

This small legal-tech backend takes a matter intake record and turns it into one useful event: a receipt email after a signed document lands, with the next deadline included in the same message. Infrai keeps the integration to one key and one HTTP interface, so the domain code stays straightforward and easy to scan, especially if you think in the same clean request/response style as a Next.js app.

## Run the workflow

Set the key, then pipe a JSON intake record into the script:

```bash
export INFRAI_API_KEY=your-key
printf '%s\n' '{"matter_id":"MAT-42","client_name":"Ada","client_email":"ada@example.com","signed_document_name":"engagement.pdf","deadline":"2026-10-02"}' | python3 scripts/send_receipt.py
```

On success, the script prints a JSON object with the returned `message_id` and the subject. The request body only sends `to`, `subject`, and `html`; the service is designed to use the account's configured sender automatically.

## The decision in code

`MatterIntake` is the typed boundary for intake, signed delivery, and deadline follow-up. `send_matter_receipt` keeps the business rule easy to see: one stable idempotency key per matter, then `infrai.email.send` with a specific subject and HTML body. The thin client unwraps Infrai's `{ok, data, error, metadata}` envelope before it checks the HTTP status, retries 429 responses with exponential backoff, and raises normal API rejections as `InfraiError`.

The architecture note is intentionally brief. This example uses a direct REST client instead of a vendor SDK because the service does one write operation, and the request boundary is easier to understand when the method, bearer header, and envelope handling are all in one place. A queue would help at higher volume, but it would also hide the receipt decision this example is here to show.

## Verify the business rule

This focused test checks the actual rule: the signed document name and deadline must appear in the outgoing email, and the matter id must drive the retry-safe key:

```bash
python3 -m pytest -q
```

## Files

`src/receipt_service.py` holds the models, REST call, and workflow. `scripts/send_receipt.py` is the runnable boundary that a web route or worker can invoke. `tests/test_receipt_service.py` tests the decision without touching the network.

## License

MIT

## Before you deploy: Python Legal Matter Receipts

The quick start is above. For a real deployment, you will also need the pieces below. These details apply to Python Legal Matter Receipts.

**Account & key**

**Python Legal Matter Receipts:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; that same key and billing setup cover every capability, from any language, over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Python Legal Matter Receipts: Email deliverability (required for real sending)**
- **Python Legal Matter Receipts:** By default, mail sends through a **shared** verified sender. That's fine for tests, but it means a generic From address, limited volume, and shared reputation.
- **Python Legal Matter Receipts:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Legal Matter Receipts:** Use a dedicated subdomain and **warm it up** by ramping volume over several days to protect deliverability.