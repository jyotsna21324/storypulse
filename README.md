# StoryPulse

I wanted to look at a simple question that matters to a platform with episodic stories: **which episodes are losing listeners, and where should the content team take a closer look?**

StoryPulse reads episode-level listening numbers and compares how many people start an episode with how many go on to the next one. It also looks at each episode against the usual continuation rate for that particular story. If an episode falls well below that baseline, it gets marked for review.

The idea is to give a content team a useful starting point instead of making them scan a long spreadsheet.

The current version:
- calculates completion, continuation and drop-off rates;
- highlights episodes with an unusually large drop;
- exports an episode-level report and a short summary;
- includes SQL queries for the same kind of analysis.

The review flag is only a pointer. It cannot tell us why someone stopped listening. Episode length, release timing, audio issues, notifications and the audience source could all affect the numbers, so a person still needs to investigate before making a content decision.

I have used made-up data in this project. It is not Kuku's data, and the results should not be read as actual platform performance.

### Run it

The project uses Python's standard library, so there is nothing extra to install.

```bash
python src/storypulse.py
```

The reports will appear in the `outputs` folder. To run the checks:

```bash
python -m unittest discover -s tests -v
```

The input columns and metric definitions are in [DATA_DICTIONARY.md](DATA_DICTIONARY.md). I have also added a short note on where AI was used in [AI_USAGE.md](AI_USAGE.md).
