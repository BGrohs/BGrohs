# Morning Briefing

Daily 5 a.m. briefing on critical vulnerabilities, cyberattacks, AI, tech, business and policy news.

- `INSTRUCTIONS.md`: run book for the scheduled session that writes each edition
- `build.py`: validates an edition, lints the spoken text, writes the F5-TTS script, updates the index
- `app/index.html`: web app with sources and read-aloud (published as a claude.ai artifact)
- `data/YYYY-MM-DD.json`: editions; `data/index.json`: archive index
- `scripts/#YYYY-MM-DD - Morning Briefing ....txt`: script for `podcast_pipeline.py` / F5-TTS

Voice it with your own clone:

    python3 podcast_pipeline.py --script "#2026-11-19 - Morning Briefing Thursday November 19 2026.txt"
