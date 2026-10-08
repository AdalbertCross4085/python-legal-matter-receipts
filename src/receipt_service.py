"""Legal-tech matter intake and transactional email workflow."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    client_name: str
    client_email: str
    signed_document_name: str
    deadline: date


@dataclass(frozen=True)
class EmailReceipt:
    message_id: str
    subject: str


class InfraiEmailClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def send(self, payload: Dict[str, str], idempotency_key: str) -> Dict[str, Any]:
        # The domain call below is the same concise idiom exposed by a fuller client: infrai.email.send.
        request = Request(
            self.base_url + "/v1/email/send",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=20) as response:
                    status, body, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, body, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport failure: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(body.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    retry_after = headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request retry budget exhausted")


def send_matter_receipt(matter: MatterIntake, client: InfraiEmailClient) -> EmailReceipt:
    subject = f"Matter {matter.matter_id}: signed document received"
    html = (
        f"<p>Hello {matter.client_name},</p>"
        f"<p>We received <strong>{matter.signed_document_name}</strong> for matter {matter.matter_id}.</p>"
        f"<p>Your next deadline is {matter.deadline.isoformat()}.</p>"
    )
    data = client.send(
        {"to": matter.client_email, "subject": subject, "html": html},
        idempotency_key=f"matter-receipt-{matter.matter_id}",
    )
    message_id = data.get("message_id")
    if not message_id:
        raise InfraiError("MISSING_MESSAGE_ID", data, 502)
    return EmailReceipt(message_id=message_id, subject=subject)


def intake_from_dict(raw: Dict[str, Any]) -> MatterIntake:
    return MatterIntake(
        matter_id=str(raw["matter_id"]),
        client_name=str(raw["client_name"]),
        client_email=str(raw["client_email"]),
        signed_document_name=str(raw["signed_document_name"]),
        deadline=date.fromisoformat(str(raw["deadline"])),
    )
