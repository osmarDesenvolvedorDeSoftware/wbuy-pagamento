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

    def test_process_webhook_builds_and_sends_messages_pix(self):
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
                "pagamento": {
                    "linha_digitavel": "0002010102122677PIXCODE",
                    "tipo_interno": "pix",
                },
            }
        }

        with mock.patch("app.wbuy.webhook.send_whats_message") as send_mock, mock.patch(
            "app.wbuy.webhook.time.sleep"
        ) as sleep_mock:
            webhook.process_webhook(payload)

        expected_phone = "5516996246673"
        lista_itens = "- Banco Indiano Madeira Entalhada e Ferro com Encosto 50 cm (qtd 1)"
        expected_msg_1 = webhook.build_msg_1(
            "Osmar",
            "10490102",
            "249.9",
            lista_itens,
            "Para concluir rapidinho, é só pagar usando o Pix Copia e Cola abaixo:",
        )
        expected_msg_2 = webhook.build_msg_2("0002010102122677PIXCODE")

        self.assertEqual(
            send_mock.call_args_list,
            [mock.call(expected_phone, expected_msg_1), mock.call(expected_phone, expected_msg_2)],
        )
        sleep_mock.assert_called_once_with(1)

    def test_process_webhook_handles_boleto_flow_and_order(self):
        payload = {
            "data": {
                "id": "55555",
                "cliente": {"nome": "Cliente Boleto", "telefone1": "(11)98888-7777"},
                "valor_total": {"total": "100.0"},
                "produtos": [
                    {"produto": "Produto Teste", "qtd": "2"},
                ],
                "pagamento": {
                    "linha_digitavel": "1234567890",
                    "paymentLink": "https://example.com/boleto.pdf",
                    "tipo_interno": "bank_billet",
                },
            }
        }

        events = []

        def fake_send_message(number, body):
            events.append(body)
            return {"status": "sent", "number": number, "body": body}

        def fake_send_media(number, file_bytes, filename):
            events.append("media")
            return {"status": "media", "number": number, "filename": filename}

        pdf_response = mock.Mock()
        pdf_response.content = b"%PDF-1.4"
        pdf_response.raise_for_status = mock.Mock()

        with (
            mock.patch(
                "app.wbuy.webhook.send_whats_message", side_effect=fake_send_message
            ) as send_mock,
            mock.patch(
                "app.wbuy.webhook.send_whats_media", side_effect=fake_send_media
            ) as media_mock,
            mock.patch("app.wbuy.webhook.requests.get", return_value=pdf_response) as get_mock,
            mock.patch("app.wbuy.webhook.time.sleep") as sleep_mock,
        ):
            webhook.process_webhook(payload)

        lista_itens = "- Produto Teste (qtd 2)"
        expected_phone = "5511988887777"
        expected_msg_1 = webhook.build_msg_1(
            "Cliente",
            "55555",
            "100.0",
            lista_itens,
            "Para concluir rapidinho, é só pagar usando o código de barras abaixo:",
        )
        expected_msg_2 = webhook.build_msg_2("1234567890")

        self.assertEqual(events, [expected_msg_1, expected_msg_2, "media"])
        self.assertEqual(
            send_mock.call_args_list,
            [mock.call(expected_phone, expected_msg_1), mock.call(expected_phone, expected_msg_2)],
        )
        media_mock.assert_called_once_with(expected_phone, b"%PDF-1.4", "boleto.pdf")
        sleep_mock.assert_has_calls([mock.call(1), mock.call(1)])
        get_mock.assert_called_once_with("https://example.com/boleto.pdf", stream=True, timeout=30)

    def test_send_whats_media_posts_file(self):
        file_bytes = b"pdf-bytes"

        with mock.patch.object(webhook, "WHATICKET_TOKEN", "TOKEN"), mock.patch(
            "app.wbuy.webhook.requests.post"
        ) as post_mock:
            response_mock = mock.Mock()
            response_mock.json.return_value = {"ok": True}
            response_mock.raise_for_status = mock.Mock()
            post_mock.return_value = response_mock

            response = webhook.send_whats_media("5511999999999", file_bytes, "boleto.pdf")

        self.assertEqual(response, {"ok": True})
        post_mock.assert_called_once()
        _, kwargs = post_mock.call_args
        self.assertEqual(kwargs["data"], {"number": "5511999999999"})
        self.assertIn("medias", kwargs["files"])
        self.assertEqual(kwargs["files"]["medias"][0], "boleto.pdf")

    def test_uses_test_number_when_env_present(self):
        payload = {
            "data": {
                "id": "10490102",
                "cliente": {"nome": "Osmar TESTE", "telefone1": "(16)99624-6673"},
                "valor_total": {"total": "249.9"},
                "produtos": [],
                "pagamento": {
                    "linha_digitavel": "0002010102122677PIXCODE",
                    "tipo_interno": "pix",
                },
            }
        }

        with mock.patch.object(webhook, "TEST_NUMBER", "5511999888777"), mock.patch(
            "app.wbuy.webhook.send_whats_message"
        ) as send_mock, mock.patch("app.wbuy.webhook.time.sleep"):
            webhook.process_webhook(payload)

        send_mock.assert_any_call(mock.ANY, mock.ANY)
        called_number = send_mock.call_args_list[0].args[0]
        self.assertEqual(called_number, "5511999888777")

    def test_normalize_phone_variations(self):
        self.assertEqual(webhook.normalize_phone("05516996246673"), "5516996246673")
        self.assertEqual(webhook.normalize_phone("016996246673"), "5516996246673")
        self.assertEqual(webhook.normalize_phone("5516996246673"), "5516996246673")
        self.assertEqual(webhook.normalize_phone("16996246673"), "5516996246673")


if __name__ == "__main__":
    unittest.main()
