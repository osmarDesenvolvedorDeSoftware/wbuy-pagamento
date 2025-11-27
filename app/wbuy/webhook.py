import os
import sys
import time
from typing import Any, Dict, List

import requests

from . import storage

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


def wrap_pix_payload(pix_payload: str) -> str:
    """Return the PIX payload wrapped in a code block to avoid Markdown parsing."""

    return f"```\n{pix_payload}\n```"


def build_closing_message() -> str:
    return (
        "E se tiver qualquer dúvida ou dificuldade pode chamar a gente por aqui mesmo.\n"
        "🙏🏻🙏🏻🙏🏻"
    )


def send_whats_media(number: str, file_bytes: bytes, filename: str) -> Dict[str, Any]:
    normalized_number = (number or "").strip()
    if not normalized_number:
        print(
            f"[whatsapp-media] Número ausente ou inválido para envio de mídia. Recebido: '{number}'"
        )
        return {"status": "skipped", "reason": "missing_number"}

    if not WHATICKET_TOKEN:
        print("[whatsapp-media] Token do Whaticket ausente. Configure WHATICKET_TOKEN/TOKEN_WHATS/TOKEN_DO_ENV.")
        return {"status": "error", "reason": "missing_token"}

    headers = {"Authorization": f"Bearer {WHATICKET_TOKEN}"}
    data = {"number": normalized_number}
    files = {"medias": (filename, file_bytes, "application/pdf")}

    print(
        f"[whatsapp-media] Payload construído para Whaticket: número={normalized_number}, arquivo={filename}"
    )

    response = requests.post(
        WHATICKET_API_URL, headers=headers, data=data, files=files, timeout=30
    )
    if not response.ok:
        print(
            f"[whatsapp-media] Erro ao enviar mídia. Status: {response.status_code}. Corpo: {response.text}"
        )
        return {
            "status": "error",
            "status_code": response.status_code,
            "response": response.text,
        }

    return response.json()


def send_whats_message(number: str, body: str) -> Dict[str, Any]:
    normalized_number = (number or "").strip()
    if not normalized_number:
        print(
            f"[whatsapp] Número ausente ou inválido para envio de mensagem. Recebido: '{number}'"
        )
        return {"status": "skipped", "reason": "missing_number"}

    if not WHATICKET_TOKEN:
        print("[whatsapp] Token do Whaticket ausente. Configure WHATICKET_TOKEN/TOKEN_WHATS/TOKEN_DO_ENV.")
        return {"status": "error", "reason": "missing_token"}

    headers = {
        "Authorization": f"Bearer {WHATICKET_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {"number": normalized_number, "body": body}

    print(f"[whatsapp] Payload construído para Whaticket: {payload}")

    response = requests.post(WHATICKET_API_URL, headers=headers, json=payload, timeout=30)
    if not response.ok:
        print(
            f"[whatsapp] Erro ao enviar mensagem. Status: {response.status_code}. Corpo: {response.text}"
        )
        return {
            "status": "error",
            "status_code": response.status_code,
            "response": response.text,
        }

    return response.json()


def _parse_lista_itens(produtos: List[Dict[str, Any]]) -> str:
    return "\n".join(
        f"- {produto['produto']} (qtd {produto['qtd']})" for produto in produtos
    )


def process_webhook(payload: Dict[str, Any]) -> None:
    nome_cliente = payload["data"]["cliente"]["nome"]
    telefone = payload["data"]["cliente"].get("telefone1", "")
    numero_do_pedido = str(payload["data"]["id"])
    valor_total = payload["data"]["valor_total"]["total"]
    lista_itens = _parse_lista_itens(payload["data"].get("produtos", []))
    pagamento = payload["data"]["pagamento"]
    tipo_pagamento = pagamento["tipo_interno"]

    if storage.is_order_processed(numero_do_pedido):
        print(f"[webhook] Pedido {numero_do_pedido} já processado. Ignorando envio duplicado.")
        return {"status": "skipped", "reason": "already_processed"}

    primeiro_nome = extract_first_name(nome_cliente)

    test_number = _get_test_number()
    normalized_phone = normalize_phone(test_number or telefone)

    if not normalized_phone:
        print(
            f"[webhook] Número de telefone ausente ou inválido para o pedido {numero_do_pedido}. Ignorando envio."
        )
        return {"status": "skipped", "reason": "missing_phone"}

    payment_instruction_pix = "Para concluir rapidinho, é só pagar usando o Pix Copia e Cola abaixo:"
    payment_instruction_boleto = (
        "Para concluir rapidinho, é só pagar usando o código de barras abaixo:"
    )

    if tipo_pagamento == "pix":
        pix_copia_cola = pagamento["linha_digitavel"]
        pix_safe = pix_copia_cola.replace("***", r"\*\*\*")
        mensagem_1 = build_msg_1(
            primeiro_nome,
            numero_do_pedido,
            valor_total,
            lista_itens,
            payment_instruction_pix,
        )
        mensagem_2 = wrap_pix_payload(pix_safe)
        mensagem_final = build_closing_message()

        print(f"[webhook] Enviando mensagem 1 para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_1)

        time.sleep(1)

        print(f"[webhook] Enviando mensagem 2 (PIX) para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_2)

        time.sleep(1)

        print(f"[webhook] Enviando mensagem final (PIX) para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_final)
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
        mensagem_final = build_closing_message()

        print(f"[webhook] Enviando mensagem 1 para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_1)

        time.sleep(1)

        print(f"[webhook] Enviando mensagem 2 (BOLETO) para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_2)

        time.sleep(1)

        print(f"[webhook] Baixando boleto em memória para {normalized_phone}")
        pdf_response = requests.get(pdf_url, stream=True, timeout=30)
        if not pdf_response.ok:
            print(
                f"[webhook] Erro ao baixar boleto. Status: {pdf_response.status_code}. Corpo: {pdf_response.text}"
            )
            return {
                "status": "error",
                "reason": "boleto_download_failed",
                "status_code": pdf_response.status_code,
            }
        pdf_bytes = pdf_response.content

        print(f"[webhook] Enviando boleto em PDF para {normalized_phone}")
        send_whats_media(normalized_phone, pdf_bytes, "boleto.pdf")

        time.sleep(1)

        print(f"[webhook] Enviando mensagem final (BOLETO) para {normalized_phone}")
        send_whats_message(normalized_phone, mensagem_final)

    storage.mark_order_processed(numero_do_pedido)

    sys.stdout.flush()


def handle_webhook(request) -> Dict[str, Any]:
    payload = request.get_json(silent=True) or {}

    process_webhook(payload)

    return {"status": "ok"}
