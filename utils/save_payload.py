import os
import time


def save_raw_payload(raw: bytes):
    os.makedirs(os.path.join("storage", "webhooks"), exist_ok=True)
    timestamp = int(time.time())
    filename = os.path.join("storage", "webhooks", f"raw_{timestamp}.txt")

    with open(filename, "wb") as file:
        file.write(raw)

    return filename
