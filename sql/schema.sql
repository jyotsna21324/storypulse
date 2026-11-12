-- StoryPulse sample schema (SQLite)
-- Data is synthetic and for demonstration only.
CREATE TABLE IF NOT EXISTS episode_metrics (
    story_id TEXT NOT NULL,
    story_title TEXT NOT NULL,
    genre TEXT NOT NULL,
    episode_number INTEGER NOT NULL CHECK (episode_number >= 1),
    episode_starts INTEGER NOT NULL CHECK (episode_starts > 0),
    episode_completions INTEGER NOT NULL CHECK (
        episode_completions >= 0 AND episode_completions <= episode_starts
    ),
    next_episode_starts INTEGER,
    PRIMARY KEY (story_id, episode_number)
);
