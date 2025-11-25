import unittest
from unittest import mock

from app import create_app
from app.wbuy import webhook


class TestWebhook(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_handle_webhook_processes_payload_and_returns_ok(self):
        payload = {"data": {}}

        with mock.patch("app.wbuy.webhook.process_webhook") as process_mock:
            response = self.client.post("/wbuy/webhook", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        process_mock.assert_called_once_with(payload)

    def test_process_webhook_builds_and_sends_messages(self):
        payload = {
            "data": {
                "id": "10490102",
                "cliente": {"nome": "Osmar TESTE", "telefone1": "(16)99624-6673"},
                "valor_total": {"total": "249.9"},
                "produtos": [
                    {
                        "produto": "Banco Indiano Madeira Entalhada e Ferro com Encosto 50 cm",
                        "qtd": "1",
                    }
                ],
                "pagamento": {"linha_digitavel": "0002010102122677PIXCODE"},
            }
        }

        with mock.patch("app.wbuy.webhook.send_whats_message") as send_mock, mock.patch(
            "app.wbuy.webhook.time.sleep"
        ) as sleep_mock:
            webhook.process_webhook(payload)

        expected_phone = "5516996246673"
        lista_itens = "Banco Indiano Madeira Entalhada e Ferro com Encosto 50 cm (qtd 1)"
        expected_msg_1 = webhook.build_msg_1("Osmar TESTE", "10490102", "249.9", lista_itens)
        expected_msg_2 = webhook.build_msg_2("0002010102122677PIXCODE")

        self.assertEqual(send_mock.call_count, 2)
        send_mock.assert_any_call(expected_phone, expected_msg_1)
        send_mock.assert_any_call(expected_phone, expected_msg_2)
        sleep_mock.assert_called_once_with(1)

    def test_normalize_phone_variations(self):
        self.assertEqual(webhook.normalize_phone("05516996246673"), "5516996246673")
        self.assertEqual(webhook.normalize_phone("016996246673"), "5516996246673")
        self.assertEqual(webhook.normalize_phone("5516996246673"), "5516996246673")
        self.assertEqual(webhook.normalize_phone("16996246673"), "5516996246673")


if __name__ == "__main__":
    unittest.main()
