from datetime import date

from src.receipt_service import MatterIntake, send_matter_receipt


class FakeClient:
    def __init__(self):
        self.payload = None

    def send(self, payload, idempotency_key):
        self.payload = (payload, idempotency_key)
        return {"message_id": "msg_test_123"}


def test_receipt_contains_signed_document_and_deadline():
    client = FakeClient()
    matter = MatterIntake("MAT-7", "Ada", "ada@example.com", "engagement.pdf", date(2026, 10, 2))
    receipt = send_matter_receipt(matter, client)
    payload, key = client.payload
    assert receipt.message_id == "msg_test_123"
    assert payload["to"] == "ada@example.com"
    assert "engagement.pdf" in payload["html"]
    assert "2026-10-02" in payload["html"]
    assert key == "matter-receipt-MAT-7"
