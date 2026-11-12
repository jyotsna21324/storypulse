import sys
import tempfile
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from storypulse import calculate_metrics, add_review_flags, read_metrics, run, write_story_report


class StoryPulseTests(unittest.TestCase):
    def test_calculates_continuation_rate(self):
        records = [{
            "story_id": "S1", "story_title": "Test", "genre": "Drama",
            "episode_number": 1, "episode_starts": 100,
            "episode_completions": 80, "next_episode_starts": 70,
        }]
        result = calculate_metrics(records)[0]
        self.assertAlmostEqual(result["continuation_rate"], 0.70)
        self.assertAlmostEqual(result["drop_off_rate"], 0.30)

    def test_final_episode_has_no_continuation_rate(self):
        records = [{
            "story_id": "S1", "story_title": "Test", "genre": "Drama",
            "episode_number": 2, "episode_starts": 70,
            "episode_completions": 60, "next_episode_starts": None,
        }]
        result = calculate_metrics(records)[0]
        self.assertIsNone(result["continuation_rate"])

    def test_flags_episode_below_story_baseline(self):
        records = []
        rates = [0.80, 0.82, 0.81, 0.50, 0.79]
        starts = 1000
        for episode, rate in enumerate(rates, start=1):
            records.append({
                "story_id": "S1", "story_title": "Test", "genre": "Drama",
                "episode_number": episode, "episode_starts": starts,
                "episode_completions": 800, "next_episode_starts": round(starts * rate),
            })
        flagged = add_review_flags(calculate_metrics(records))
        self.assertEqual(flagged[3]["review_flag"], "Review")

    def test_story_report_has_one_row_per_story(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = read_metrics(ROOT / "data" / "sample_episode_metrics.csv")
            metrics = add_review_flags(calculate_metrics(records))
            report = Path(tmp) / "story_summary.csv"
            write_story_report(metrics, report)
            with report.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 8)

    def test_end_to_end_creates_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            episode_report, summary = run(
                ROOT / "data" / "sample_episode_metrics.csv", out
            )
            self.assertTrue(episode_report.exists())
            self.assertTrue(summary.exists())
            self.assertTrue((out / "story_summary.csv").exists())


if __name__ == "__main__":
    unittest.main()
