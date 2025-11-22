from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
WEBHOOK_DIR = BASE_DIR / "storage" / "webhooks"


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
