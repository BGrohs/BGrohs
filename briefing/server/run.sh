#!/usr/bin/env bash
# Daily run: collect feeds -> Claude writes the edition -> build -> publish to SITE_DIR -> git -> ntfy.
# Started by the systemd timer (see setup.sh). Safe to run by hand: briefing/server/run.sh
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
source briefing/server/config.env

DATE="$(TZ=Europe/Berlin date +%F)"
WORK="briefing/work"
LOG="$WORK/$DATE.log"
DIGEST="$WORK/$DATE-feeds.md"
mkdir -p "$WORK" "$SITE_DIR/data" "$SITE_DIR/scripts"
exec > >(tee -a "$LOG") 2>&1
echo "=== $(date -Is) morning briefing $DATE"

notify() {  # notify <title> <message> [priority] [tags]
  local auth=()
  [ -n "${NTFY_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $NTFY_TOKEN")
  curl -fsS "${auth[@]}" -H "Title: $1" -H "Click: ${SITE_URL}#d-$DATE" \
       -H "Priority: ${3:-default}" -H "Tags: ${4:-newspaper}" -d "$2" \
       "$NTFY_URL/$NTFY_TOPIC" >/dev/null || echo "ntfy push failed"
}
fail() { echo "FAILED: $1"; notify "Morning Briefing failed" "$1. Log: $REPO/$LOG" high warning; exit 1; }

git pull -q --ff-only || echo "git pull failed, continuing with local copy"

python3 briefing/collect.py --hours 30 --out "$DIGEST" || fail "Feed collection failed"

PROMPT="$(sed -e "s|{{DATE}}|$DATE|g" -e "s|{{DIGEST}}|$DIGEST|g" briefing/server/PROMPT.md)"
timeout "${CLAUDE_TIMEOUT:-5400}" "${CLAUDE_BIN:-claude}" -p "$PROMPT" \
  --model "${CLAUDE_MODEL:-sonnet}" \
  --permission-mode acceptEdits \
  --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "WebSearch" "WebFetch" "Agent" "Task" \
                 "Bash(python3 briefing/build.py:*)" \
  || fail "Claude writing step failed or timed out"

[ -f "briefing/data/$DATE.json" ] || fail "No edition file was written"
python3 briefing/build.py "briefing/data/$DATE.json" || fail "Build failed"

# Publish the static site (served by tailscale serve).
cp briefing/app/index.html "$SITE_DIR/index.html"
cp briefing/data/*.json "$SITE_DIR/data/"
cp briefing/scripts/????-??-??.txt "$SITE_DIR/scripts/" 2>/dev/null || true

git add briefing/data briefing/scripts
git commit -qm "Morning briefing $DATE" || true
[ "${GIT_PUSH:-0}" = "1" ] && { git push -q || echo "git push failed (edition is still published locally)"; }

# Push notification with the top headlines.
mapfile -t N < <(python3 - "$DATE" <<'EOF'
import json, sys
from datetime import date
d = sys.argv[1]
b = json.load(open(f"briefing/data/{d}.json"))
crit = any(i["severity"] == "critical" and any("xploit" in t for t in i.get("tags", []))
           for s in b["sections"] for i in s["items"])
st = b["stats"]
title = "Morning Briefing " + date.fromisoformat(d).strftime("%a %-d %b")
msg = f"{st['items']} stories, ~{st['minutes']} min. Top: " + "; ".join(b["headlines"][:3])
print("\n".join([title, msg, "high" if crit else "default", "newspaper,rotating_light" if crit else "newspaper"]))
EOF
)
notify "${N[0]}" "${N[1]}" "${N[2]}" "${N[3]}"
echo "=== $(date -Is) done"
