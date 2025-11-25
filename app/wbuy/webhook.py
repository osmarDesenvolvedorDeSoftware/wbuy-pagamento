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


def _get_test_number() -> str:
    """
    Return the configured test phone number, if any.

    The value is read from the first non-empty environment variable among:
    - WHATSAPP_TEST_NUMBER (current)
    - NUMBER_TEST (value present in the repo's .env)
    - NUMBER_TESTE (legacy documentation)
    """

    for env_key in ("WHATSAPP_TEST_NUMBER", "NUMBER_TEST", "NUMBER_TESTE"):
        value = os.getenv(env_key)
        if value:
            return value

    return ""


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())

    while digits.startswith("0"):
        digits = digits[1:]

    if digits.startswith("55"):
        return digits

    if len(digits) == 11:
        return f"55{digits}"

    return digits


def extract_first_name(full_name: str) -> str:
    full_name = (full_name or "").strip()
    return full_name.split()[0] if full_name else ""


def build_msg_1(
    nome_cliente: str,
    numero_do_pedido: str,
    valor_total: str,
    lista_itens: str,
    payment_instruction: str,
) -> str:
    itens_formatados = f"\n{lista_itens}" if lista_itens else ""

    return (
        f"Oi, {nome_cliente}! 🌺✨\n"
        "Aqui é a Carol da Sarat.\n"
        "Espero que esteja tudo bem?\n"
        "Que alegria ver seu pedido chegando pra gente 💛\n"
        f"Aqui estão os dados certinhos do seu pedido {numero_do_pedido}:\n\n"
        f"📦 Pedido: {numero_do_pedido}\n"
        f"🧾 Valor total: R$ {valor_total}\n"
        f"🛍️ Itens:{itens_formatados}\n\n"
        f"{payment_instruction}"
    )


def build_msg_2(pix_copia_cola: str) -> str:
    return pix_copia_cola


def send_whats_media(number: str, file_bytes: bytes, filename: str) -> Dict[str, Any]:
    if not WHATICKET_TOKEN:
        raise RuntimeError("Missing Whaticket token. Set WHATICKET_TOKEN/TOKEN_WHATS/TOKEN_DO_ENV.")

    headers = {"Authorization": f"Bearer {WHATICKET_TOKEN}"}
    data = {"number": number}
    files = {"medias": (filename, file_bytes, "application/pdf")}

    response = requests.post(
        WHATICKET_API_URL, headers=headers, data=data, files=files, timeout=30
    )
    response.raise_for_status()

    return response.json()


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
    return "\n".join(
        f"- {produto['produto']} (qtd {produto['qtd']})" for produto in produtos
    )


def process_webhook(payload: Dict[str, Any]) -> None:
    nome_cliente = payload["data"]["cliente"]["nome"]
    telefone = payload["data"]["cliente"]["telefone1"]
    numero_do_pedido = payload["data"]["id"]
    valor_total = payload["data"]["valor_total"]["total"]
    lista_itens = _parse_lista_itens(payload["data"].get("produtos", []))
    pagamento = payload["data"]["pagamento"]
    tipo_pagamento = pagamento["tipo_interno"]

    primeiro_nome = extract_first_name(nome_cliente)

    test_number = _get_test_number()
    normalized_phone = normalize_phone(test_number or telefone)

    payment_instruction_pix = "Para concluir rapidinho, é só pagar usando o Pix Copia e Cola abaixo:"
    payment_instruction_boleto = (
        "Para concluir rapidinho, é só pagar usando o código de barras abaixo:"
    )

    if tipo_pagamento == "pix":
        pix_copia_cola = pagamento["linha_digitavel"]
        mensagem_1 = build_msg_1(
            primeiro_nome,
            numero_do_pedido,
            valor_total,
            lista_itens,
            payment_instruction_pix,
        )
        mensagem_2 = build_msg_2(pix_copia_cola)

        print(f"[webhook] Enviando mensagem 1 para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_1)

        time.sleep(1)

        print(f"[webhook] Enviando mensagem 2 (PIX) para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_2)
    elif tipo_pagamento == "bank_billet":
        codigo_barras = pagamento["linha_digitavel"]
        pdf_url = pagamento["paymentLink"]
        mensagem_1 = build_msg_1(
            primeiro_nome,
            numero_do_pedido,
            valor_total,
            lista_itens,
            payment_instruction_boleto,
        )
        mensagem_2 = build_msg_2(codigo_barras)

        print(f"[webhook] Enviando mensagem 1 para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_1)

        time.sleep(1)

        print(f"[webhook] Enviando mensagem 2 (BOLETO) para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_2)

        time.sleep(1)

        print(f"[webhook] Baixando boleto em memória para {normalized_phone}")
        pdf_response = requests.get(pdf_url, stream=True, timeout=30)
        pdf_response.raise_for_status()
        pdf_bytes = pdf_response.content

        print(f"[webhook] Enviando boleto em PDF para {normalized_phone}")
        send_whats_media(normalized_phone, pdf_bytes, "boleto.pdf")

    sys.stdout.flush()


def handle_webhook(request) -> Dict[str, Any]:
    payload = request.get_json(silent=True) or {}

    process_webhook(payload)

    return {"status": "ok"}
