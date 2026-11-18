Write today's Daily Morning Briefing. Date: {{DATE}} (Europe/Berlin).

1. Read `briefing/INSTRUCTIONS.md` and follow its sections "Coverage window and focus",
   "Sections and what goes in them", "Research method", "Writing", "Spoken-text rules" and
   "JSON schema". Skip its "Publishing" section: the wrapper script that started you
   publishes, commits and sends the push.
2. Start from the feed digest at `{{DIGEST}}`. It lists the last 30 hours of headlines
   from about 35 feeds with direct links, plus the CISA KEV additions. Choose the stories
   from it, open the important articles with WebFetch to verify the facts, and use
   WebSearch only to fill gaps (vendor advisories, CVSS scores, stories the feeds missed).
   If a site blocks you, use another source for the same story.
3. To keep your context small, you may research the sections in parallel with subagents.
4. Write `briefing/data/{{DATE}}.json`, then run `python3 briefing/build.py briefing/data/{{DATE}}.json`.
   Fix every error and lint warning in the spoken text, and rerun until it is clean.
5. Do not run git, curl or any publishing step. Finish with one line: the number of
   stories and the estimated minutes.
