from datetime import datetime
from pathlib import Path
from typing import Set


BASE_DIR = Path(__file__).resolve().parents[2]
WEBHOOK_DIR = BASE_DIR / "storage" / "webhooks"
PROCESSED_FILE = BASE_DIR / "storage" / "processed_orders.txt"


def save_raw_payload(raw_bytes: bytes) -> str:
    """
    Salva o webhook cru em storage/webhooks/raw_<timestamp>.txt
    Cria pastas se necessário.
    Retorna o caminho salvo.
    """
    WEBHOOK_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    file_path = WEBHOOK_DIR / f"raw_{timestamp}.txt"

    with open(file_path, "wb") as file:
        file.write(raw_bytes)

    return str(file_path)


def _read_processed_orders() -> Set[str]:
    if not PROCESSED_FILE.exists():
        return set()

    return {line.strip() for line in PROCESSED_FILE.read_text().splitlines() if line.strip()}


def is_order_processed(order_id: str) -> bool:
    """
    Verifica se o pedido já foi processado anteriormente.
    """

    return order_id in _read_processed_orders()


def mark_order_processed(order_id: str) -> None:
    """
    Registra que um pedido foi processado, evitando envios duplicados.
    """

    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)

    processed = _read_processed_orders()
    if order_id in processed:
        return

    with open(PROCESSED_FILE, "a", encoding="utf-8") as file:
        file.write(f"{order_id}\n")
