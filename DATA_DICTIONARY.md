# Data dictionary

All rows in `data/sample_episode_metrics.csv` are synthetic and created for demonstration.

| Field | Type | Description |
|---|---|---|
| story_id | text | Stable identifier for the story |
| story_title | text | Story display title |
| genre | text | Broad story category |
| episode_number | integer | Episode sequence number |
| episode_starts | integer | Number of listeners/starts for this episode |
| episode_completions | integer | Number of starts that reached the completion event |
| next_episode_starts | integer or blank | Number who started the next episode; blank for final episode |

## Metric definitions

- Completion rate = episode_completions / episode_starts
- Continuation rate = next_episode_starts / episode_starts
- Drop-off rate = 1 - continuation rate

For a real platform, definitions must be aligned with analytics instrumentation. For example, a product team may use unique listeners rather than play events, and may define a fixed time window for continuation.
