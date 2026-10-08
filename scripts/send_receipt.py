import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.receipt_service import InfraiEmailClient, intake_from_dict, send_matter_receipt


def main() -> None:
    raw = json.loads(sys.stdin.read())
    receipt = send_matter_receipt(intake_from_dict(raw), InfraiEmailClient())
    print(json.dumps({"message_id": receipt.message_id, "subject": receipt.subject}))


if __name__ == "__main__":
    main()
