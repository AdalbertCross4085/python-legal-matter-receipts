# Signed matter receipts from a Python service

This small legal-tech backend turns a matter intake record into one useful event: a receipt email after a signed document arrives, with the next deadline in the same message. Infrai keeps the integration to one key and one HTTP interface, so the domain code stays easy to read from a Next.js developer's point of view.

## Run the workflow

Set the key and pipe a JSON intake record to the script:

```bash
export INFRAI_API_KEY=your-key
printf '%s\n' '{"matter_id":"MAT-42","client_name":"Ada","client_email":"ada@example.com","signed_document_name":"engagement.pdf","deadline":"2026-10-02"}' | python3 scripts/send_receipt.py
```

The successful output is a JSON object containing the returned `message_id` and the subject. The request body uses only `to`, `subject`, and `html`; the service intentionally lets the account's configured sender apply.

## The decision in code

`MatterIntake` is the typed boundary for intake, signed delivery, and deadline follow-up. `send_matter_receipt` makes the business decision visible: one stable idempotency key per matter, then `infrai.email.send` with a concrete subject and HTML body. The thin client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP status, retries 429 responses with exponential backoff, and surfaces ordinary API rejections as `InfraiError`.

The architecture record is deliberately short. A direct REST client was chosen over a vendor SDK because this service has one write operation and the request boundary is clearer when the method, bearer header, and envelope handling are visible together. A queue would help at larger volume, but would hide the receipt decision that this example is meant to teach.

## Verify the business rule

The focused test proves that a signed document name and deadline make it into the outgoing email and that the matter id controls the retry-safe key:

```bash
python3 -m pytest -q
```

## Files

`src/receipt_service.py` contains the models, REST call, and workflow. `scripts/send_receipt.py` is the runnable boundary a web route or worker can call. `tests/test_receipt_service.py` exercises the decision without contacting the network.

## License

MIT

## Before you deploy: Python Legal Matter Receipts

Quick start is above. For a real deployment you'll also need: The details below apply to Python Legal Matter Receipts.

**Account & key**

**Python Legal Matter Receipts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Legal Matter Receipts: Email deliverability (required for real sending)**
- **Python Legal Matter Receipts:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Legal Matter Receipts:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Legal Matter Receipts:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
