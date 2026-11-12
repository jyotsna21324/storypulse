"""StoryPulse: a small, explainable episode-retention analysis tool.

The project uses synthetic sample data. It does not access Kuku's internal data.
Run from the repository root:
    python src/storypulse.py
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "sample_episode_metrics.csv"
DEFAULT_OUTPUT = ROOT / "outputs"


def read_metrics(path: Path) -> list[dict]:
    """Read and validate episode metrics from a CSV file."""
    required = {
        "story_id", "story_title", "genre", "episode_number",
        "episode_starts", "episode_completions", "next_episode_starts",
    }
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        records = []
        for line_number, row in enumerate(reader, start=2):
            try:
                starts = int(row["episode_starts"])
                completions = int(row["episode_completions"])
                next_starts = (
                    int(row["next_episode_starts"])
                    if row["next_episode_starts"].strip()
                    else None
                )
                episode_number = int(row["episode_number"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value on CSV line {line_number}") from exc

            if starts <= 0:
                raise ValueError(f"episode_starts must be positive on line {line_number}")
            if not 0 <= completions <= starts:
                raise ValueError(f"Completions must be between 0 and starts on line {line_number}")
            if next_starts is not None and not 0 <= next_starts <= starts:
                raise ValueError(f"Next-episode starts must be between 0 and starts on line {line_number}")
            if episode_number < 1:
                raise ValueError(f"episode_number must be positive on line {line_number}")

            records.append({
                **row,
                "episode_number": episode_number,
                "episode_starts": starts,
                "episode_completions": completions,
                "next_episode_starts": next_starts,
            })
    return records


def calculate_metrics(records: list[dict]) -> list[dict]:
    """Calculate completion and continuation rates for each episode."""
    results = []
    for row in records:
        starts = row["episode_starts"]
        next_starts = row["next_episode_starts"]
        results.append({
            "story_id": row["story_id"],
            "story_title": row["story_title"],
            "genre": row["genre"],
            "episode_number": row["episode_number"],
            "episode_starts": starts,
            "episode_completions": row["episode_completions"],
            "completion_rate": row["episode_completions"] / starts,
            "next_episode_starts": next_starts,
            "continuation_rate": next_starts / starts if next_starts is not None else None,
            "drop_off_rate": 1 - (next_starts / starts) if next_starts is not None else None,
        })
    return results


def add_review_flags(metrics: list[dict], gap_threshold: float = 0.15) -> list[dict]:
    """Flag episodes materially below their own story's median continuation rate.

    This is a triage signal for human review, not proof that an episode caused churn.
    """
    by_story = defaultdict(list)
    for row in metrics:
        if row["continuation_rate"] is not None:
            by_story[row["story_id"]].append(row["continuation_rate"])

    medians = {story_id: median(rates) for story_id, rates in by_story.items()}
    flagged = []
    for row in metrics:
        result = dict(row)
        baseline = medians.get(row["story_id"])
        result["story_median_continuation"] = baseline
        if row["continuation_rate"] is None:
            result["review_flag"] = "Final episode - no next episode"
            result["review_reason"] = "Continuation is not applicable to the final episode."
        elif row["continuation_rate"] <= baseline - gap_threshold:
            result["review_flag"] = "Review"
            result["review_reason"] = (
                f"Continuation is at least {gap_threshold:.0%} below this story's median."
            )
        else:
            result["review_flag"] = "No flag"
            result["review_reason"] = ""
        flagged.append(result)
    return flagged


def write_episode_report(metrics: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "story_id", "story_title", "genre", "episode_number", "episode_starts",
        "episode_completions", "completion_rate", "next_episode_starts",
        "continuation_rate", "drop_off_rate", "story_median_continuation",
        "review_flag", "review_reason",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in metrics:
            formatted = dict(row)
            for key in ("completion_rate", "continuation_rate", "drop_off_rate", "story_median_continuation"):
                value = formatted.get(key)
                formatted[key] = "" if value is None else round(value, 4)
            writer.writerow(formatted)


def write_story_report(metrics: list[dict], output_path: Path) -> None:
    """Write one row per story, excluding final episodes from continuation averages."""
    by_story = defaultdict(list)
    for row in metrics:
        by_story[row["story_id"]].append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "story_id", "story_title", "genre", "episodes_analyzed",
        "average_completion_rate", "average_continuation_rate",
        "episodes_flagged",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for story_id, story_rows in sorted(by_story.items()):
            continuation = [
                row["continuation_rate"] for row in story_rows
                if row["continuation_rate"] is not None
            ]
            completion = [row["completion_rate"] for row in story_rows]
            writer.writerow({
                "story_id": story_id,
                "story_title": story_rows[0]["story_title"],
                "genre": story_rows[0]["genre"],
                "episodes_analyzed": len(story_rows),
                "average_completion_rate": round(sum(completion) / len(completion), 4),
                "average_continuation_rate": (
                    round(sum(continuation) / len(continuation), 4)
                    if continuation else ""
                ),
                "episodes_flagged": sum(row["review_flag"] == "Review" for row in story_rows),
            })


def build_summary(metrics: list[dict]) -> str:
    """Create a concise, human-readable summary from calculated metrics."""
    by_story = defaultdict(list)
    for row in metrics:
        by_story[row["story_id"]].append(row)

    flagged = [r for r in metrics if r["review_flag"] == "Review"]
    lines = [
        "# StoryPulse - Analysis Summary",
        "",
        "> This report uses synthetic demonstration data. It is not Kuku user data.",
        "",
        f"- Stories analyzed: **{len(by_story)}**",
        f"- Episode records analyzed: **{len(metrics)}**",
        f"- Episodes flagged for human review: **{len(flagged)}**",
        "",
        "## Episodes to review",
        "",
    ]
    if not flagged:
        lines.append("No episodes crossed the review threshold in this dataset.")
    else:
        for row in sorted(flagged, key=lambda x: x["continuation_rate"]):
            lines.append(
                f"- **{row['story_title']} - Episode {row['episode_number']}**: "
                f"{row['continuation_rate']:.1%} continued to the next episode. "
                f"Story median: {row['story_median_continuation']:.1%}."
            )

    lines.extend([
        "",
        "## How to interpret this",
        "",
        "A review flag means an episode's continuation rate is unusually low compared "
        "with the median for its own story. It is a prompt for investigation, not a "
        "causal conclusion. The team should consider episode length, release timing, "
        "marketing, audio quality, platform issues and audience mix before changing content.",
        "",
        "## Suggested next steps",
        "",
        "1. Listen to the flagged episodes and compare them with the episode before and after.",
        "2. Check whether the drop appears across listener cohorts or only one segment.",
        "3. Review release timing and any app/audio incidents around the same period.",
        "4. Record the team's finding and compare retention after any change.",
        "",
    ])
    return "\n".join(lines)


def run(input_path: Path = DEFAULT_INPUT, output_dir: Path = DEFAULT_OUTPUT) -> tuple[Path, Path]:
    records = read_metrics(input_path)
    metrics = add_review_flags(calculate_metrics(records))
    episode_path = output_dir / "episode_analysis.csv"
    story_path = output_dir / "story_summary.csv"
    summary_path = output_dir / "analysis_summary.md"
    write_episode_report(metrics, episode_path)
    write_story_report(metrics, story_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(build_summary(metrics), encoding="utf-8")
    return episode_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze episode-level listener retention.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input episode metrics CSV")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Folder for generated reports")
    args = parser.parse_args()
    episode_path, summary_path = run(args.input, args.output_dir)
    print(f"Analysis complete.\nEpisode report: {episode_path}\nSummary: {summary_path}")


if __name__ == "__main__":
    main()
