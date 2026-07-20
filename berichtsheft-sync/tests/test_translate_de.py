import unittest

from berichtsheft.translate_de import translate_note_to_de


class TestTranslateDe(unittest.TestCase):
    def test_coffee_break_no_double(self):
        out = translate_note_to_de("coffee break tagung ruang 3")
        self.assertNotIn("Break-Break", out)
        self.assertIn("Coffee-Break", out)

    def test_indonesian_buffet(self):
        out = translate_note_to_de("membereskan buffet, mencuci piring")
        self.assertIn("Buffet", out)
        self.assertNotIn("mencuci", out.lower())

    def test_summary_de(self):
        out = translate_note_to_de("Shift Tagung beendet")
        self.assertIn("Tagung", out)
        self.assertNotIn("Shift Tagung beendet", out)


if __name__ == "__main__":
    unittest.main()
