import sys
from typing import Any, Dict

from .storage import save_raw_payload


def handle_webhook(request) -> Dict[str, Any]:
    """
    Recebe request do Flask, salva payload, e no futuro vai
    acionar processamento do pedido.
    """
    raw_payload = request.get_data(cache=False, as_text=False, parse_form_data=False) or b""

    save_raw_payload(raw_payload)

    sys.stdout.buffer.write(raw_payload + b"\n")
    sys.stdout.flush()

    return {"status": "ok"}
