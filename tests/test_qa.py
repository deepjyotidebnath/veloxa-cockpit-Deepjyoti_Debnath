"""Runs every question in qa_cases.json through the cockpit and checks status + required/forbidden text."""
import json
import pathlib
import unittest
from cockpit.ask import ask

CASES = json.loads((pathlib.Path(__file__).parent / "qa_cases.json").read_text())


class QA(unittest.TestCase):
    def test_enough_cases(self):
        self.assertGreaterEqual(len(CASES), 25)
        self.assertGreaterEqual(sum(c["kind"] in ("refuse", "uncertain") for c in CASES), 5)

    def test_cases(self):
        for c in CASES:
            with self.subTest(c["id"], q=c["question"]):
                a = ask(c["question"], known_by=c["known_by"], as_of=c["as_of"])
                text = a.render()
                self.assertEqual(a.status, c["expect_status"], text)
                for s in c["must_contain"]:
                    self.assertIn(s, text)
                for s in c["must_not_contain"]:
                    self.assertNotIn(s, text)
                if c["expect_status"] == "answered" or c["expect_status"] == "disagree":
                    self.assertTrue(a.cites, "an answer must cite records")
                    self.assertIsNotNone(a.confidence, "an answer must state confidence")


if __name__ == "__main__":
    unittest.main()
