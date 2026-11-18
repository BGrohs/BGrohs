# Morning Briefing

Daily 5 a.m. briefing on critical vulnerabilities, cyberattacks, AI, tech, business and policy news.

- `INSTRUCTIONS.md`: run book for the scheduled session that writes each edition
- `build.py`: validates an edition, lints the spoken text, writes the F5-TTS script, updates the index
- `app/index.html`: web app with sources and read-aloud (published as a claude.ai artifact)
- `data/YYYY-MM-DD.json`: editions; `data/index.json`: archive index
- `scripts/#YYYY-MM-DD - Morning Briefing ....txt`: script for `podcast_pipeline.py` / F5-TTS

Voice it with your own clone:

    python3 podcast_pipeline.py --script "#2026-11-19 - Morning Briefing Thursday November 19 2026.txt"

## Running on your own server (Tailscale)

    git clone -b claude/daily-morning-briefing-yjrq7t https://github.com/BGrohs/BGrohs.git ~/morning-briefing
    cd ~/morning-briefing
    bash briefing/server/setup.sh        # config, systemd timer (04:00 Europe/Berlin), tailscale serve
    nano briefing/server/config.env      # SITE_URL from `tailscale serve status`, optional NTFY_TOKEN
    briefing/server/run.sh               # first test run, log in briefing/work/<date>.log

`collect.py` pulls ~35 RSS feeds plus the CISA KEV catalog (`server/feeds.txt`), Claude Code
(`claude -p`, subscription login) writes the edition from that digest, and `run.sh` builds,
copies the site to `SITE_DIR`, commits, and sends the ntfy push.
