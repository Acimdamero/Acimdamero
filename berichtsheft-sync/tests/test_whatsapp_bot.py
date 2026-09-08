"""Tests for WhatsApp (WAHA) Berichtsheft bot helpers."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from berichtsheft.whatsapp_bot import (
    NUMBER_MAP,
    _is_allowed,
    menu_text,
    normalize_chat_id,
    parse_waha_webhook,
)


class TestWhatsAppBot(unittest.TestCase):
    def test_normalize_chat_id(self) -> None:
        self.assertEqual(normalize_chat_id("6281234567890"), "6281234567890@c.us")
        self.assertEqual(normalize_chat_id("+6281234567890"), "6281234567890@c.us")
        self.assertEqual(normalize_chat_id("081234567890"), "6281234567890@c.us")
        self.assertEqual(
            normalize_chat_id("6281234567890@c.us"), "6281234567890@c.us"
        )
        self.assertEqual(normalize_chat_id(""), "")

    def test_menu_text_has_options(self) -> None:
        text = menu_text()
        self.assertIn("Selesai", text)
        self.assertIn("OK", text)
        self.assertIn("Minggu", text)
        self.assertIn("1 ·", text)

    def test_number_map(self) -> None:
        self.assertIn("2", NUMBER_MAP)
        self.assertIn("menu", NUMBER_MAP)
        self.assertEqual(NUMBER_MAP["m"], NUMBER_MAP["menu"])

    def test_parse_waha_webhook(self) -> None:
        payload = {
            "event": "message",
            "payload": {
                "from": "628111@c.us",
                "body": "halo",
                "fromMe": False,
            },
        }
        parsed = parse_waha_webhook(payload)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        chat_id, text, from_me = parsed
        self.assertEqual(chat_id, "628111@c.us")
        self.assertEqual(text, "halo")
        self.assertFalse(from_me)

    def test_parse_waha_webhook_ignores_empty(self) -> None:
        self.assertIsNone(parse_waha_webhook({"event": "message", "payload": {}}))

    def test_allowed_empty_rejects_all(self) -> None:
        with mock.patch.dict(os.environ, {"WHATSAPP_ALLOWED_NUMBER": ""}, clear=False):
            self.assertFalse(_is_allowed("628111@c.us"))

    def test_allowed_number_matches(self) -> None:
        with mock.patch.dict(
            os.environ, {"WHATSAPP_ALLOWED_NUMBER": "628111"}, clear=False
        ):
            self.assertTrue(_is_allowed("628111@c.us"))
            self.assertFalse(_is_allowed("628999@c.us"))


if __name__ == "__main__":
    unittest.main()
