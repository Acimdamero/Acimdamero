import unittest

from berichtsheft.blok_status import detect_week_status


class FakeLocator:
    def __init__(self, count: int):
        self._count = count

    def count(self) -> int:
        return self._count


class FakePage:
    def __init__(self, body: str, textarea_count: int = 1, editmode: int = 0):
        self._body = body
        self._textarea_count = textarea_count
        self._editmode = editmode

    def inner_text(self, _selector: str) -> str:
        return self._body

    def locator(self, selector: str) -> FakeLocator:
        if "textarea" in selector:
            return FakeLocator(self._textarea_count)
        if "editmode" in selector or "Bearbeitungsmodus" in selector:
            return FakeLocator(self._editmode)
        return FakeLocator(0)


class TestBlokStatus(unittest.TestCase):
    def test_bearbeitbar(self):
        page = FakePage("Kalenderwoche vom 01.06.2026", textarea_count=7)
        info = detect_week_status(page)
        self.assertEqual(info["status"], "bearbeitbar")
        self.assertTrue(info["editable"])

    def test_abgenommen_locked(self):
        page = FakePage("Diese Woche wurde abgenommen.", textarea_count=0)
        info = detect_week_status(page)
        self.assertEqual(info["status"], "abgenommen")
        self.assertTrue(info["locked"])
        self.assertFalse(info["editable"])

    def test_abgenommen_with_editmode(self):
        page = FakePage(
            "abgenommen Bearbeitungsmodus",
            textarea_count=7,
            editmode=1,
        )
        info = detect_week_status(page)
        self.assertTrue(info["has_editmode"])
        self.assertTrue(info["editable"])


if __name__ == "__main__":
    unittest.main()
