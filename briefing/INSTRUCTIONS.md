# Daily Morning Briefing: run book

This file is the job description for the scheduled session that produces the briefing
every morning. Follow it step by step. The reader is one person (an IT leader in the
DACH region) who listens to the briefing on a roughly 60 minute drive and skims the
web page for sources and actions.

## Output, in short

1. `briefing/data/YYYY-MM-DD.json`: the briefing (schema below), in **English**.
2. `python3 briefing/build.py briefing/data/YYYY-MM-DD.json`: validates the JSON, lints
   the spoken text, writes `briefing/scripts/#YYYY-MM-DD - Morning Briefing ....txt`
   (F5-TTS format) plus `briefing/scripts/YYYY-MM-DD.txt`, and updates
   `briefing/data/index.json`.
3. Publish the web app with the new data (the artifact URL is given in the task prompt).
4. Commit and push.
5. Send the ntfy push (topic given in the task prompt).

## Coverage window and focus

- Window: news published since the previous briefing, which is normally the last 24 hours
  (use about 30 hours to catch late items). Use today's date in Europe/Berlin.
- Before researching, read the last three files in `briefing/data/` and do not repeat
  their stories. A real development on an older story is fine: prefix the headline with
  `Update:` and only tell what is new.
- Weighting: tech and AI news are the core; security is broad; business and policy are
  shorter. Global coverage with an eye on Europe and the DACH region (BSI, CERT.at,
  NIS2, DORA, EU AI Act, European companies).

## Sections and what goes in them

Use these section ids in this order. Leave a section's `items` empty only if there is
truly nothing; the build skips it in the audio.

| id | title | content | items |
|---|---|---|---|
| `vulns` | Critical Vulnerabilities | CVSS 9.0+, new CISA KEV entries, actively exploited zero-days, emergency patches, important vendor advisories (Microsoft, Apple, Google/Chrome, Cisco, Fortinet, Palo Alto, Ivanti, Citrix, VMware/Broadcom, SAP, Atlassian, Linux kernel, OpenSSL, popular OSS libraries, AI tooling). High-severity bugs in very widely used software also count. | 6 to 12 |
| `attacks` | Cyberattacks & Breaches | Major ransomware incidents, data breaches, supply-chain compromises, state-sponsored campaigns, DDoS on critical services, law-enforcement takedowns and arrests. | 4 to 8 |
| `ai` | AI | Model releases, lab news (OpenAI, Anthropic, Google, Meta, Mistral, xAI, DeepSeek and others), agents and tooling, notable research, AI in the enterprise, AI chips and compute deals, AI safety and AI security. | 6 to 10 |
| `tech` | Tech & Industry | Big tech, cloud, semiconductors, devices, software platforms, developer ecosystem, outages. | 4 to 8 |
| `business` | Business & Markets | Earnings that matter for tech, M&A, funding rounds, layoffs, market moves. | 3 to 6 |
| `policy` | Regulation & Policy | EU, Germany, Austria, US and UK regulation, court rulings, antitrust, export controls. | 2 to 5 |

### Severity chip (`severity`)

- `critical`: act today. Exploited in the wild, CVSS 9+, or a major incident with direct impact.
- `high`: important, act or watch this week.
- `notable`: good to know.

Order items within each section by severity, then by importance.

## Research method

- Use WebSearch and WebFetch. To keep your context small, you may spawn one research
  subagent per section in parallel. Give each one the window, the section brief above
  and the list of headlines already covered, and have it return candidate stories with
  verified facts and source URLs.
- Fetch the CISA KEV catalog directly and list entries whose `dateAdded` falls in the
  window:
  `curl -s https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
- Good sources include CISA, NVD, vendor PSIRT pages, BSI, CERT.at, BleepingComputer,
  The Record, SecurityWeek, The Hacker News, Help Net Security, Dark Reading, Krebs on
  Security, Reuters, Bloomberg, Financial Times, CNBC, The Verge, TechCrunch, Ars Technica,
  Wired, heise, Golem, Handelsblatt, the official blogs of AI labs, and arXiv.
- **Accuracy rules. These are not optional.**
  - Every item needs at least one source URL that you actually saw in a search result or
    fetched. Prefer primary sources (advisory, vendor post, filing) plus one news report.
  - Never invent or guess CVE ids, CVSS scores, version numbers, victim names, figures,
    or quotes. If a number is not confirmed, leave it out.
  - Check the publication date of every story. It must fall in the window.
  - Attribute claims that are unconfirmed ("according to Reuters", "the group claims").

## Writing

Every item has two layers:

- **Page layer** (`headline`, `summary`, `why`, `action`, `tags`): written text that is
  compact and skimmable. Here numbers, CVE ids, versions and acronyms are welcome.
  `summary` is at most 2 to 3 sentences (about 60 words). `why` is one sentence on why it
  matters to an IT or business leader. `action` (optional, mostly for vulns and attacks)
  is a concrete next step, such as "Patch FortiOS to 7.6.4; check for IOCs listed in the
  advisory". `tags` are short chips, such as `CVE-2026-12345`, `CVSS 9.8`, `KEV`,
  `Exploited`, `Microsoft`, `Ransomware`, `EU`.
- **Audio layer** (`spoken`): the podcast narration of the story, read aloud by a TTS
  voice (browser speech and an F5-TTS voice clone). Explain the context, what happened,
  who is affected and what to do. Give lead stories 300 to 450 words and smaller items
  120 to 220 words. Split it into paragraphs with blank lines.

The intro (`intro`, about 200 to 300 words) greets the listener, names the date and
previews the three to five biggest stories. Each section has a short `spoken_intro`
transition of one or two sentences. Vary it from day to day. The outro (`outro`, about
100 to 150 words) recaps the must-do actions for today and signs off.

**Target length: 7,000 to 9,000 spoken words in total, about 50 to 60 minutes.** On a slow
news day, go deeper on the big stories rather than padding with trivia.

### Spoken-text rules (the build lints these)

- No digits. Spell numbers out: "nine point eight", "twenty twenty-six", "three million".
  Version numbers become "version seven point six point four", or just say "the latest
  version" when the exact number adds nothing.
- Do not read CVE ids aloud. Name the product and the bug instead; the page carries the id.
- No markdown, URLs, brackets, slashes used as "or", or em dashes. Write e.g., i.e., etc.
  and vs. out as words.
- Expand acronyms on first use unless they are universal (IT, CEO, AI, CPU, EU, US).
  "Remote code execution" rather than "RCE". "CISA, the US Cybersecurity and
  Infrastructure Security Agency" the first time it appears each day.
- Punctuate for breath. Use short sentences, write conversationally, like a sharp
  colleague briefing you on the drive in. No hype words, no filler.

## JSON schema

```json
{
  "date": "2026-11-18",
  "title": "Short title for the archive, naming the top two or three stories",
  "description": "Three to five sentences of flowing prose for the podcast description.",
  "headlines": ["Top story one-liner", "...", "..."],
  "intro": "Spoken intro. Paragraphs separated by blank lines.",
  "sections": [
    {
      "id": "vulns",
      "title": "Critical Vulnerabilities",
      "spoken_intro": "Let's start with what needs patching.",
      "items": [
        {
          "id": "vulns-1",
          "headline": "Fortinet patches exploited FortiOS SSL-VPN flaw",
          "severity": "critical",
          "tags": ["CVE-2026-12345", "CVSS 9.8", "KEV", "Exploited"],
          "summary": "Written summary, numbers allowed.",
          "why": "One sentence on why it matters.",
          "action": "Optional concrete next step.",
          "spoken": "Spoken narration for the item.\n\nSecond paragraph.",
          "sources": [{"name": "Fortinet PSIRT", "url": "https://..."}]
        }
      ]
    }
  ],
  "outro": "Spoken outro."
}
```

Item ids are `<section>-<n>`. `build.py` adds `stats` and `generated_at` to the file.

## Publishing

1. Run `python3 briefing/build.py briefing/data/<date>.json`. Fix every error, and fix
   lint warnings by editing the spoken text. Rerun until it is clean or only harmless
   warnings remain.
2. Read the artifact first (Artifact tool, `action: "read"`, `url` from the task prompt),
   then publish to that same `url`, with `file_path: briefing/app/index.html` and
   `files` set to:
   ```json
   {
     "data/index.json": "briefing/data/index.json",
     "data/<date>.json": "briefing/data/<date>.json",
     "scripts/<date>.txt": "briefing/scripts/<date>.txt"
   }
   ```
   Files you leave out (older days) stay published. Do not pass `icon`.
3. Commit `briefing/data`, `briefing/scripts` with the message
   `Morning briefing <date>`, and push to the branch named in the task prompt.
4. Send the push notification:
   ```bash
   curl -s -H "Title: Morning Briefing <Weekday, d Month>" \
        -H "Click: <artifact url>#d-<date>" \
        -H "Tags: newspaper" -H "Priority: default" \
        -d "<N> stories, ~<M> min. Top: <headline 1>; <headline 2>; <headline 3>" \
        https://ntfy.sh/<topic>
   ```
   Use `Priority: high` and add the `rotating_light` tag when at least one item is
   `critical` and exploited in the wild.

If anything fails (for example the artifact publish), still commit what you have and
send the ntfy push with a short note on what failed. If the artifact could not be
updated, link to the script file on GitHub instead.
