import unittest

from berichtsheft.blok_fields import resolve_day_fields
from berichtsheft.blok_mapping import abteilung_for_shift

SAMPLE_MAPPING = {
    "presence": {
        "arbeit": "Anwesend",
        "schule": "Anwesend",
        "frei": "Abwesend",
    },
    "location": {
        "arbeit": "Ausbildungsbetrieb",
        "schule": "Berufsschule",
    },
    "weekend_arbeit_presence": "Anwesend",
    "abteilung": {
        "default": "",
        "BRF": "Service",
        "HK": "Housekeeping",
        "Schule": "Berufsschule",
    },
}


class TestBlokFields(unittest.TestCase):
    def test_arbeit_weekday(self):
        shift = {"day_type": "arbeit", "tags": ["BRF"]}
        fields = resolve_day_fields(shift, day_idx=2, mapping=SAMPLE_MAPPING)
        self.assertEqual(fields["presence"], "Anwesend")
        self.assertEqual(fields["location"], "Ausbildungsbetrieb")
        self.assertEqual(fields["abteilung"], "Service")

    def test_schule(self):
        shift = {"day_type": "schule", "tags": []}
        fields = resolve_day_fields(shift, day_idx=0, mapping=SAMPLE_MAPPING)
        self.assertEqual(fields["presence"], "Anwesend")
        self.assertEqual(fields["location"], "Berufsschule")
        self.assertEqual(fields["abteilung"], "Berufsschule")

    def test_frei(self):
        shift = {"day_type": "frei", "tags": []}
        fields = resolve_day_fields(shift, day_idx=3, mapping=SAMPLE_MAPPING)
        self.assertEqual(fields["presence"], "Abwesend")
        self.assertNotIn("location", fields)

    def test_weekend_arbeit_anwesend(self):
        shift = {"day_type": "arbeit", "tags": ["BRF", "HK"]}
        fields = resolve_day_fields(shift, day_idx=5, mapping=SAMPLE_MAPPING)
        self.assertEqual(fields["presence"], "Anwesend")
        self.assertEqual(fields["location"], "Ausbildungsbetrieb")

    def test_sunday_arbeit(self):
        shift = {"day_type": "arbeit", "tags": ["BRF"]}
        fields = resolve_day_fields(shift, day_idx=6, mapping=SAMPLE_MAPPING)
        self.assertEqual(fields["presence"], "Anwesend")

    def test_abteilung_tag_priority(self):
        shift = {"day_type": "arbeit", "tags": ["HK", "BRF"]}
        self.assertEqual(abteilung_for_shift(SAMPLE_MAPPING, shift), "Housekeeping")

    def test_abteilung_default_empty(self):
        shift = {"day_type": "arbeit", "tags": []}
        fields = resolve_day_fields(shift, day_idx=1, mapping=SAMPLE_MAPPING)
        self.assertNotIn("abteilung", fields)


class TestBlokAuditParse(unittest.TestCase):
    def test_parse_readonly_days(self):
        from berichtsheft.blok_audit import _parse_readonly_days

        body = (
            "Mo 01.06.\nBerufsschule\nAnwesend\n8h:00min\nLernen im Unterricht\n\n"
            "Di 02.06.\nAusbildungsbetrieb\nAnwesend\n0h:00min\n"
        )
        chunks = _parse_readonly_days(body)
        self.assertIn("Mo", chunks)
        self.assertIn("Lernen im Unterricht", chunks["Mo"])
        self.assertIn("Di", chunks)


if __name__ == "__main__":
    unittest.main()
