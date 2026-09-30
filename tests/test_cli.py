import unittest

from travel.cli import parse_args


class CliTests(unittest.TestCase):
    def test_accepts_required_date_aliases(self):
        self.assertEqual(parse_args(["-date", "2028-02-29"]).travel_date, "2028-02-29")
        self.assertEqual(parse_args(["--date", "2026-10-15"]).travel_date, "2026-10-15")

    def test_missing_or_invalid_date_exits_with_usage(self):
        for argv in ([], ["-date", "2026-02-30"], ["-date", "2026-9-1"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as raised:
                parse_args(argv)
            self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
