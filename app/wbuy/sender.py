import os
import requests
from typing import Dict


def send_whatsapp_message(number: str, message: str) -> Dict:
    """
    Envia mensagem via Whaticket (API Messages/Send)
    Usa:
      URL_WHATS → API base (ex: https://api.osmardev.online/api/messages/send)
      TOKEN_WHATS → Bearer token
      NUMBER_TESTE → opcional; se existir, sobrescreve o número de destino
    """
    pass
