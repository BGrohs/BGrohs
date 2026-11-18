#!/usr/bin/env python3
"""Collect the last N hours of headlines from RSS/Atom feeds and the CISA KEV catalog.

Usage: python3 briefing/collect.py [--hours 30] [--out briefing/work/YYYY-MM-DD-feeds.md]
Writes a compact Markdown digest that the writing step starts from. Standard library only.
"""
import argparse
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (X11; Linux x86_64) MorningBriefing/1.0 (personal feed reader)"
KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def clean(text, n=280):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n] + ("…" if len(text) > n else "")


def parse_feed(raw):
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):  # RSS 2.0
        items.append({
            "title": it.findtext("title"), "link": it.findtext("link"),
            "date": parse_date(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")),
            "summary": it.findtext("description"),
        })
    for e in root.iter("{http://www.w3.org/2005/Atom}entry"):  # Atom
        link = e.find("atom:link[@rel='alternate']", NS)
        if link is None:
            link = e.find("atom:link", NS)
        items.append({
            "title": e.findtext("atom:title", namespaces=NS),
            "link": link.get("href") if link is not None else None,
            "date": parse_date(e.findtext("atom:published", namespaces=NS) or e.findtext("atom:updated", namespaces=NS)),
            "summary": e.findtext("atom:summary", namespaces=NS) or e.findtext("atom:content", namespaces=NS),
        })
    return items


def load_feeds():
    feeds = []
    for line in (ROOT / "server" / "feeds.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            sec, name, url = [p.strip() for p in line.split("|", 2)]
            feeds.append((sec, name, url))
    return feeds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=30)
    ap.add_argument("--out")
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=a.hours)

    def one(feed):
        sec, name, url = feed
        try:
            items = [i for i in parse_feed(fetch(url)) if i["title"] and i["link"]]
            fresh = [i for i in items if i["date"] and i["date"] >= since]
            return feed, fresh, None
        except Exception as e:  # noqa: BLE001 - report and continue
            return feed, [], f"{type(e).__name__}: {e}"[:120]

    with ThreadPoolExecutor(12) as ex:
        results = list(ex.map(one, load_feeds()))

    seen, by_sec, failed = set(), {}, []
    for (sec, name, url), items, err in results:
        if err:
            failed.append(f"{name} ({url}): {err}")
        for i in sorted(items, key=lambda x: x["date"], reverse=True):
            key = re.sub(r"\W+", "", i["title"].lower())[:80]
            if key in seen:
                continue
            seen.add(key)
            by_sec.setdefault(sec, []).append((name, i))

    kev_lines, kev_err = [], None
    try:
        kev = json.loads(fetch(KEV))
        cutoff = (now - timedelta(hours=max(a.hours, 48))).date().isoformat()
        for v in kev["vulnerabilities"]:
            if v["dateAdded"] >= cutoff:
                kev_lines.append(f"- {v['cveID']} | {v['vendorProject']} {v['product']} | {v['vulnerabilityName']} | added {v['dateAdded']} | ransomware: {v.get('knownRansomwareCampaignUse', 'Unknown')}")
    except Exception as e:  # noqa: BLE001
        kev_err = str(e)[:120]

    out = [f"# Feed digest {now.astimezone().strftime('%Y-%m-%d %H:%M %Z')} (last {a.hours} h)", ""]
    out += ["## CISA KEV additions (last 48 h)", *(kev_lines or [f"- none{' (fetch failed: ' + kev_err + ')' if kev_err else ''}"]), ""]
    for sec in ["vulns", "attacks", "ai", "tech", "business", "policy"]:
        out.append(f"## {sec}")
        for name, i in by_sec.get(sec, []):
            out.append(f"- [{name}] {clean(i['title'], 200)} ({i['date'].strftime('%m-%d %H:%M')}Z) {i['link'].strip()}")
            s = clean(i["summary"])
            if s:
                out.append(f"  {s}")
        out.append("")
    if failed:
        out += ["## Feeds that failed", *[f"- {f}" for f in failed], ""]

    text = "\n".join(out)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    n = sum(len(v) for v in by_sec.values())
    print(f"collected {n} items from {len(results) - len(failed)}/{len(results)} feeds, {len(kev_lines)} KEV additions", file=sys.stderr)
    for f in failed:
        print("  failed:", f, file=sys.stderr)


if __name__ == "__main__":
    main()
