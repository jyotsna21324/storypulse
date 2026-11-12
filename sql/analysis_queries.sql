-- StoryPulse analysis queries (SQLite)
-- Import data/sample_episode_metrics.csv into episode_metrics before running.

-- 1. Episode-level completion and continuation rates.
SELECT
    story_id,
    story_title,
    genre,
    episode_number,
    episode_starts,
    ROUND(1.0 * episode_completions / episode_starts, 4) AS completion_rate,
    CASE
        WHEN next_episode_starts IS NULL THEN NULL
        ELSE ROUND(1.0 * next_episode_starts / episode_starts, 4)
    END AS continuation_rate,
    CASE
        WHEN next_episode_starts IS NULL THEN NULL
        ELSE ROUND(1.0 - 1.0 * next_episode_starts / episode_starts, 4)
    END AS drop_off_rate
FROM episode_metrics
ORDER BY story_id, episode_number;

-- 2. Stories ranked by average continuation rate (final episodes excluded).
SELECT
    story_id,
    story_title,
    genre,
    ROUND(AVG(1.0 * next_episode_starts / episode_starts), 4) AS avg_continuation
FROM episode_metrics
WHERE next_episode_starts IS NOT NULL
GROUP BY story_id, story_title, genre
ORDER BY avg_continuation DESC;

-- 3. Episode-level outliers relative to each story's average.
-- The Python version uses the median for a more robust baseline.
WITH episode_rates AS (
    SELECT
        story_id,
        story_title,
        episode_number,
        1.0 * next_episode_starts / episode_starts AS continuation_rate
    FROM episode_metrics
    WHERE next_episode_starts IS NOT NULL
),
story_baselines AS (
    SELECT story_id, AVG(continuation_rate) AS avg_story_continuation
    FROM episode_rates
    GROUP BY story_id
)
SELECT
    e.story_id,
    e.story_title,
    e.episode_number,
    ROUND(e.continuation_rate, 4) AS continuation_rate,
    ROUND(b.avg_story_continuation, 4) AS avg_story_continuation
FROM episode_rates e
JOIN story_baselines b USING (story_id)
WHERE e.continuation_rate <= b.avg_story_continuation - 0.15
ORDER BY e.continuation_rate;
