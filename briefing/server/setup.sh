#!/usr/bin/env bash
# One-time setup on the server. Run from the repo root as your normal user:
#   bash briefing/server/setup.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
chmod +x briefing/server/run.sh

# 1. Config
if [ ! -f briefing/server/config.env ]; then
  cp briefing/server/config.example.env briefing/server/config.env
  echo "Created briefing/server/config.env. Edit SITE_URL / NTFY_TOKEN if needed."
fi
grep -qxF 'briefing/server/config.env' .gitignore 2>/dev/null || printf 'briefing/server/config.env\nbriefing/work/\n' >> .gitignore
source briefing/server/config.env
mkdir -p "$SITE_DIR/data" "$SITE_DIR/scripts"
cp briefing/app/index.html "$SITE_DIR/"
cp briefing/data/*.json "$SITE_DIR/data/" 2>/dev/null || true
cp briefing/scripts/????-??-??.txt "$SITE_DIR/scripts/" 2>/dev/null || true

# 2. Checks
command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
command -v "${CLAUDE_BIN:-claude}" >/dev/null || echo "WARNING: claude not found in PATH (set CLAUDE_BIN in config.env)"
command -v tailscale >/dev/null || echo "WARNING: tailscale not found"

# 3. systemd user timer: daily 04:00 Europe/Berlin, catches up after downtime.
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/morning-briefing.service <<EOF
[Unit]
Description=Daily Morning Briefing
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$REPO
Environment=PATH=$HOME/.local/bin:$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/env bash $REPO/briefing/server/run.sh
TimeoutStartSec=2h
EOF
cat > ~/.config/systemd/user/morning-briefing.timer <<'EOF'
[Unit]
Description=Daily Morning Briefing at 04:00 Europe/Berlin

[Timer]
OnCalendar=*-*-* 04:00:00 Europe/Berlin
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now morning-briefing.timer
sudo loginctl enable-linger "$USER"   # run the timer even when you are not logged in

# 4. Serve the site inside the tailnet over HTTPS (needed for copy button and screen wake lock).
sudo tailscale serve --bg --set-path /briefing "$SITE_DIR"
tailscale serve status || true

echo
echo "Done. Next run: $(systemctl --user list-timers morning-briefing.timer --no-legend | awk '{print $1, $2, $3}')"
echo "Test now with:  briefing/server/run.sh     (log in briefing/work/<date>.log)"
