"""Evolution API messaging service."""

import requests
from bet.config import settings


def send_message(number: str, url: str, text: str, quoted_key_id: str | None = None):
    payload = {
        "number": f"{number}",  # "5588996245635",
        "text": f"*Aviso de gol:*\n{text}",
    }
    if quoted_key_id:
        if "quoted" not in payload:
            payload["quoted"] = {}

        if "key" not in payload["quoted"]:
            payload["quoted"]["key"] = {}

        payload["quoted"]["key"]["id"] = f"{quoted_key_id}"

    headers = {"apikey": f"{settings.instance_key}", "Content-Type": "application/json"}

    response = requests.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()
