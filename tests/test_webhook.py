import io
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List
from unittest import mock

from app import create_app
from app.wbuy import storage


class TestWebhookReceiver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_dir = storage.WEBHOOK_DIR
        storage.WEBHOOK_DIR = Path(self.temp_dir.name)

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        storage.WEBHOOK_DIR = self.original_dir
        self.temp_dir.cleanup()

    def _list_saved_files(self) -> List[Path]:
        return list(Path(self.temp_dir.name).glob("raw_*.txt"))

    def test_webhook_saves_raw_bytes_and_returns_ok(self):
        payload = b"random bytes \x00\x01with text"

        response = self.client.post("/wbuy/webhook", data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

        saved_files = self._list_saved_files()
        self.assertEqual(len(saved_files), 1)

        saved_content = saved_files[0].read_bytes()
        self.assertEqual(saved_content, payload)

    def test_handle_webhook_logs_payload(self):
        payload = b"payload to log"

        fake_stdout = type("Stdout", (), {"buffer": io.BytesIO(), "flush": lambda self: None})()

        with mock.patch("sys.stdout", fake_stdout):
            response = self.client.post("/wbuy/webhook", data=payload)

        self.assertEqual(response.status_code, 200)
        fake_stdout.buffer.seek(0)
        self.assertEqual(fake_stdout.buffer.read(), payload + b"\n")
