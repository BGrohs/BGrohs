#!/usr/bin/env python3
"""Validate a daily briefing JSON, lint its spoken text, write the F5-TTS script
and update the archive index.

Usage:  python3 briefing/build.py briefing/data/YYYY-MM-DD.json
Exit code 1 on schema errors. Lint warnings are printed but do not fail the build;
fix them anyway, because the spoken text is read aloud verbatim.
"""
import json
import re
import sys
from datetime import date as Date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"

SECTION_IDS = ["vulns", "attacks", "ai", "tech", "business", "policy"]
SEVERITIES = {"critical", "high", "notable"}
WPM = 145  # spoken words per minute used for the duration estimate

LINT_RULES = [
    (re.compile(r"\d"), "digit (spell numbers out)"),
    (re.compile(r"https?://|www\."), "URL"),
    (re.compile(r"[*_#`\[\]|<>]"), "markdown/markup character"),
    (re.compile(r"\b(e\.g\.|i\.e\.|etc\.|vs\.)", re.I), "written abbreviation"),
    (re.compile(r"[—–]"), "em/en dash (use a comma or full stop)"),
    (re.compile(r"\bCVE-", re.I), "raw CVE id (say it in words or leave it to the page)"),
]


def fail(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def lint(label, text, warnings):
    for rx, why in LINT_RULES:
        m = rx.search(text)
        if m:
            start = max(0, m.start() - 30)
            warnings.append(f"{label}: {why}: ...{text[start:m.end() + 30]!r}...")


def words(text):
    return len(re.findall(r"\b\w+\b", text))


def validate(b):
    for key in ("date", "title", "description", "intro", "outro", "headlines", "sections"):
        if key not in b:
            fail(f"missing top-level key '{key}'")
    try:
        Date.fromisoformat(b["date"])
    except ValueError:
        fail("date must be YYYY-MM-DD")
    if not 3 <= len(b["headlines"]) <= 6:
        fail("headlines: give 3 to 6 one-line top stories")
    ids = set()
    for s in b["sections"]:
        if s.get("id") not in SECTION_IDS:
            fail(f"section id {s.get('id')!r} not in {SECTION_IDS}")
        for key in ("title", "spoken_intro", "items"):
            if key not in s:
                fail(f"section {s['id']}: missing '{key}'")
        for it in s["items"]:
            for key in ("id", "headline", "severity", "summary", "why", "spoken", "sources"):
                if not it.get(key):
                    fail(f"item {it.get('id') or it.get('headline')}: missing '{key}'")
            if it["id"] in ids:
                fail(f"duplicate item id {it['id']}")
            ids.add(it["id"])
            if it["severity"] not in SEVERITIES:
                fail(f"item {it['id']}: severity must be one of {sorted(SEVERITIES)}")
            for src in it["sources"]:
                if not src.get("name") or not str(src.get("url", "")).startswith("http"):
                    fail(f"item {it['id']}: every source needs a name and an http(s) url")


def spoken_parts(b):
    """The spoken script as an ordered list of paragraphs (same order the web app reads)."""
    parts = [p for p in b["intro"].split("\n\n") if p.strip()]
    for s in b["sections"]:
        if not s["items"]:
            continue
        parts.append(s["spoken_intro"].strip())
        for it in s["items"]:
            parts += [p.strip() for p in it["spoken"].split("\n\n") if p.strip()]
    parts += [p for p in b["outro"].split("\n\n") if p.strip()]
    return parts


def main():
    if len(sys.argv) != 2:
        fail(__doc__)
    path = Path(sys.argv[1])
    b = json.loads(path.read_text(encoding="utf-8"))
    validate(b)

    warnings = []
    lint("intro", b["intro"], warnings)
    lint("outro", b["outro"], warnings)
    for s in b["sections"]:
        lint(f"{s['id']}.spoken_intro", s["spoken_intro"], warnings)
        for it in s["items"]:
            lint(f"{it['id']}.spoken", it["spoken"], warnings)

    parts = spoken_parts(b)
    total_words = sum(words(p) for p in parts)
    minutes = round(total_words / WPM)
    n_items = sum(len(s["items"]) for s in b["sections"])
    n_sources = sum(len(it["sources"]) for s in b["sections"] for it in s["items"])

    b["stats"] = {"words": total_words, "minutes": minutes, "items": n_items, "sources": n_sources}
    b.setdefault("generated_at", datetime.now(timezone.utc).isoformat(timespec="minutes"))
    path.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # F5-TTS script, same layout as the podcast_pipeline.py input files.
    d = Date.fromisoformat(b["date"])
    title = f"#{b['date']} - Morning Briefing {d.strftime('%A %B')} {d.day} {d.year}"
    outlets = sorted({src["name"] for s in b["sections"] for it in s["items"] for src in it["sources"]})
    txt = (
        f"{title}\n\nDESCRIPTION\n-----------\n{b['description'].strip()}\n\n"
        f"FULL SCRIPT\n-----------\n" + "\n\n".join(parts) + "\n\n---\n"
        f"Source: Daily tech, AI and security news roundup. Outlets: {', '.join(outlets)}\n"
        f"Generated: {Date.today().isoformat()}\n"
    )
    SCRIPTS.mkdir(exist_ok=True)
    for old in SCRIPTS.glob(f"#{b['date']} - *.txt"):
        old.unlink()
    (SCRIPTS / f"{title}.txt").write_text(txt, encoding="utf-8")
    (SCRIPTS / f"{b['date']}.txt").write_text(txt, encoding="utf-8")  # stable name for the web app

    # Archive index, newest first.
    idx_path = DATA / "index.json"
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {"briefings": []}
    entry = {"date": b["date"], "title": b["title"], "minutes": minutes, "items": n_items}
    idx["briefings"] = [e for e in idx["briefings"] if e["date"] != b["date"]] + [entry]
    idx["briefings"].sort(key=lambda e: e["date"], reverse=True)
    idx["latest"] = idx["briefings"][0]["date"]
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK {b['date']}: {n_items} items, {n_sources} sources, {total_words} spoken words (~{minutes} min)")
    print(f"Script: {SCRIPTS / (title + '.txt')}")
    if warnings:
        print(f"\n{len(warnings)} lint warning(s) in spoken text:")
        for w in warnings:
            print("  -", w)


if __name__ == "__main__":
    main()
