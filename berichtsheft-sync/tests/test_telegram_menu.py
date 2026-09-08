"""Tests for Telegram menu keyboard mapping."""

from __future__ import annotations

import unittest

from berichtsheft.telegram_bot import (
    BTN_AUDIT,
    BTN_HELP,
    BTN_LOG,
    BTN_MINGGU,
    BTN_OK,
    BTN_SELESAI,
    BTN_STATUS,
    MENU_ACTIONS,
    _main_menu_keyboard,
    _resolve_menu_text,
)


class TestTelegramMenu(unittest.TestCase):
    def test_keyboard_has_rows(self) -> None:
        kb = _main_menu_keyboard()
        self.assertTrue(kb["resize_keyboard"])
        self.assertEqual(len(kb["keyboard"]), 4)
        labels = [btn["text"] for row in kb["keyboard"] for btn in row]
        self.assertIn(BTN_SELESAI, labels)
        self.assertIn(BTN_OK, labels)
        self.assertIn(BTN_MINGGU, labels)

    def test_resolve_direct_commands(self) -> None:
        self.assertEqual(_resolve_menu_text(BTN_SELESAI), "/selesai")
        self.assertEqual(_resolve_menu_text(BTN_STATUS), "/status")
        self.assertEqual(_resolve_menu_text(BTN_OK), "/ok")
        self.assertEqual(_resolve_menu_text(BTN_AUDIT), "/audit")
        self.assertEqual(_resolve_menu_text(BTN_HELP), "/help")

    def test_resolve_prompts(self) -> None:
        self.assertEqual(_resolve_menu_text(BTN_LOG), "__prompt_log__")
        self.assertIsNone(_resolve_menu_text("teks biasa bukan tombol"))

    def test_menu_actions_cover_keyboard(self) -> None:
        labels = [btn["text"] for row in _main_menu_keyboard()["keyboard"] for btn in row]
        for label in labels:
            self.assertIn(label, MENU_ACTIONS)


if __name__ == "__main__":
    unittest.main()
