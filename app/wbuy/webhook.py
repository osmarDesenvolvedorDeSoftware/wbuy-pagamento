import os
import sys
import time
from typing import Any, Dict, List

import requests

WHATICKET_API_URL = os.getenv(
    "WHATICKET_API_BASE_URL", "https://api.osmardev.online/api/messages/send"
)
WHATICKET_TOKEN = (
    os.getenv("TOKEN_DO_ENV")
    or os.getenv("WHATICKET_TOKEN")
    or os.getenv("TOKEN_WHATS")
)


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())

    while digits.startswith("0"):
        digits = digits[1:]

    if digits.startswith("55"):
        return digits

    if len(digits) == 11:
        return f"55{digits}"

    return digits


def build_msg_1(nome_cliente: str, numero_do_pedido: str, valor_total: str, lista_itens: str) -> str:
    return (
        f"Oi, {nome_cliente}! 🌺✨\n"
        "Aqui é a Carol da Sarat.\n"
        "Espero que esteja tudo bem?\n"
        "Que alegria ver seu pedido chegando pra gente 💛\n"
        f"Aqui estão os dados certinhos do seu pedido {numero_do_pedido}:\n\n"
        f"📦 Pedido: {numero_do_pedido}\n"
        f"🧾 Valor total: R$ {valor_total}\n"
        f"🛍️ Itens: {lista_itens}\n\n"
        "Para concluir rapidinho, é só pagar usando o Pix Copia e Cola abaixo:"
    )


def build_msg_2(pix_copia_cola: str) -> str:
    return pix_copia_cola


def send_whats_message(number: str, body: str) -> Dict[str, Any]:
    if not WHATICKET_TOKEN:
        raise RuntimeError("Missing Whaticket token. Set WHATICKET_TOKEN/TOKEN_WHATS/TOKEN_DO_ENV.")

    headers = {
        "Authorization": f"Bearer {WHATICKET_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {"number": number, "body": body}

    response = requests.post(WHATICKET_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()


def _parse_lista_itens(produtos: List[Dict[str, Any]]) -> str:
    return ", ".join(f"{produto['produto']} (qtd {produto['qtd']})" for produto in produtos)


def process_webhook(payload: Dict[str, Any]) -> None:
    nome_cliente = payload["data"]["cliente"]["nome"]
    telefone = payload["data"]["cliente"]["telefone1"]
    numero_do_pedido = payload["data"]["id"]
    valor_total = payload["data"]["valor_total"]["total"]
    lista_itens = _parse_lista_itens(payload["data"].get("produtos", []))
    pix_copia_cola = payload["data"]["pagamento"]["linha_digitavel"]

    normalized_phone = normalize_phone(telefone)

    mensagem_1 = build_msg_1(nome_cliente, numero_do_pedido, valor_total, lista_itens)
    mensagem_2 = build_msg_2(pix_copia_cola)

    print(f"[webhook] Enviando mensagem 1 para {normalized_phone}")
    send_whats_message(normalized_phone, mensagem_1)

    time.sleep(1)

    print(f"[webhook] Enviando mensagem 2 (PIX) para {normalized_phone}")
    send_whats_message(normalized_phone, mensagem_2)

    sys.stdout.flush()


def handle_webhook(request) -> Dict[str, Any]:
    payload = request.get_json(silent=True) or {}

    process_webhook(payload)

    return {"status": "ok"}
