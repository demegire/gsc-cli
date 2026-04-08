# gsc-cli

Agent-first CLI for Google Search Console SEO analytics.

Designed for both humans and AI agents — outputs structured JSON when piped, rich tables when interactive.

## Install

```bash
pip install gsc-cli
```

Or from source:

```bash
git clone https://github.com/demegire/gsc-cli.git
cd gsc-cli
pip install -e .
```

## Example

```
$ gsc query --site sc-domain:imagetextedit.com --dimensions query --row-limit 15

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ query                             ┃ clicks ┃ impressions ┃    ctr ┃ position ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ imagetextedit                     │   2144 │        3863 │  0.555 │      1.1 │
│ image text edit                   │    387 │        1242 │ 0.3116 │      3.4 │
│ photext                           │    232 │       20829 │ 0.0111 │      5.5 │
│ imagetextedit.com                 │    195 │         330 │ 0.5909 │        1 │
│ edit text in image                │    118 │        1582 │ 0.0746 │      9.6 │
│ image text edit.com               │    116 │         185 │  0.627 │        1 │
│ screenshot text editor            │     86 │         423 │ 0.2033 │     12.2 │
│ image text editor                 │     82 │        1080 │ 0.0759 │     10.4 │
│ screenshot editor                 │     63 │         327 │ 0.1927 │     22.0 │
│ how to edit text in jpeg image    │     60 │         787 │ 0.0762 │      5.7 │
│ online                            │        │             │        │          │
│ edit text in image with same font │     58 │         548 │ 0.1058 │      6.7 │
│ how to edit text in image         │     57 │        1109 │ 0.0514 │      5.9 │
│ image textedit                    │     56 │         101 │ 0.5545 │      1.4 │
│ edit text in image ai             │     51 │         548 │ 0.0931 │      5.8 │
│ edit text in image ai free        │     48 │         567 │ 0.0847 │      3.8 │
└───────────────────────────────────┴────────┴─────────────┴────────┴──────────┘
```

When piped, output switches to structured JSON automatically:

```
$ gsc query --site sc-domain:imagetextedit.com --dimensions device | jq .
{
  "ok": true,
  "data": [
    {"device": "MOBILE",  "clicks": 11744, "impressions": 137664, "ctr": 0.0853, "position": 6.2},
    {"device": "DESKTOP", "clicks": 4289,  "impressions": 102507, "ctr": 0.0418, "position": 9.8},
    {"device": "TABLET",  "clicks": 203,   "impressions": 1835,   "ctr": 0.1106, "position": 5.8}
  ],
  "meta": {"row_count": 3, "site": "sc-domain:imagetextedit.com", ...}
}
```

### Feed it to an AI agent for analysis

Because `gsc` outputs structured JSON when piped, you can feed it directly into any AI agent. Here's what Claude found when analyzing a real site:

```
$ gsc query -s sc-domain:imagetextedit.com -d country --row-limit 10 | \
  claude -p "Analyze this SEO data. What stands out?"

Key findings:

1. India dominates (37% of clicks) with strong position 6.2 and 9.9% CTR
2. USA underperforms badly — 57k impressions but only 1.5k clicks (2.7% CTR),
   avg position 12.3. You're getting shown but not clicked in the US market.
3. Philippines and Indonesia punch above weight with 10%+ CTR
4. English-speaking markets (US, UK, Canada, Australia) all have worse
   positions (10-12) vs developing markets (4-6), suggesting stronger
   competition in English SERPs
```

```
$ gsc query -s sc-domain:imagetextedit.com -d date | \
  claude -p "Any anomalies in this traffic data?"

ALERT: Massive traffic cliff on March 25.
- Before (Mar 11-24): ~1,044 clicks/day, position 6.9
- After (Mar 25+): ~132 clicks/day, position 26.6
- That's an 87% drop in clicks and positions fell from page 1 to page 3+

The remaining traffic is almost entirely branded queries ("imagetextedit").
All non-brand queries like "edit text in image" dropped from position 9.6
to 44.1. This pattern is consistent with a Google algorithmic penalty.

Recommended: Check Search Console for manual actions, review robots.txt
changes around Mar 24-25, and check for a Google core update on that date.
```

## Authentication

You need credentials from [Google Cloud Console](https://console.cloud.google.com/). Enable the **Google Search Console API** in your project first.

### Option A: OAuth (interactive, personal use)

1. Go to **APIs & Services > Credentials > Create Credentials > OAuth Client ID**
2. Application type: **Desktop app**
3. Download the JSON file

```bash
gsc auth login --client-secrets ~/Downloads/client_secret_*.json
```

A browser opens for authorization. Credentials are cached — only needed once.

### Option B: Service Account (headless, automation)

1. Go to **APIs & Services > Credentials > Create Credentials > Service Account**
2. Create a key: **Keys tab > Add Key > JSON**
3. In [Search Console](https://search.google.com/search-console/), go to **Settings > Users and permissions > Add User** and paste the service account email with **Full** access

```bash
gsc auth service-account --key-file ~/path/to/key.json
```

### Check status

```bash
gsc auth status
```

## Usage

### Query search analytics

```bash
# Top queries (last 28 days)
gsc query --site sc-domain:example.com --dimensions query

# Top pages with click data
gsc query --site sc-domain:example.com --dimensions page --row-limit 50

# Filter by keyword
gsc query -s sc-domain:example.com -d query --filter "query contains python"

# Multi-dimensional analysis
gsc query -s sc-domain:example.com -d query,page --format csv

# Date trend
gsc query -s sc-domain:example.com -d date

# Regex filter
gsc query -s sc-domain:example.com -d query --filter "query includingRegex ^how to"

# Fetch all results (auto-pagination)
gsc query -s sc-domain:example.com -d query --all

# Fresh (non-final) data
gsc query -s sc-domain:example.com -d date --data-state all
```

### List sites

```bash
gsc sites list
```

### Inspect a URL

```bash
gsc inspect https://example.com/page --site sc-domain:example.com
```

## Output formats

| Flag | When | Description |
|------|------|-------------|
| `--format json` | Default when piped | Structured JSON envelope |
| `--format table` | Default in terminal | Rich table with colors |
| `--format csv` | Explicit | CSV to stdout |

### JSON envelope

Every JSON response follows this contract:

```json
{
  "ok": true,
  "data": [...],
  "meta": {
    "row_count": 25,
    "site": "sc-domain:example.com",
    "date_range": ["2026-03-11", "2026-04-07"]
  }
}
```

Errors:

```json
{
  "ok": false,
  "error": {
    "code": "AUTH_MISSING",
    "message": "No credentials found. Run: gsc auth login",
    "details": null
  }
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication error |
| 4 | API error (quota, permission) |
| 5 | No results |

## Query options

| Flag | Description |
|------|-------------|
| `--site`, `-s` | Site URL (required). e.g. `sc-domain:example.com` |
| `--dimensions`, `-d` | Comma-separated: `query`, `page`, `country`, `device`, `date`, `searchAppearance` |
| `--filter` | Repeatable. Format: `"dimension operator value"` |
| `--search-type`, `-t` | `web` (default), `image`, `video`, `news`, `discover`, `googleNews` |
| `--start-date` | `YYYY-MM-DD` (default: 28 days ago) |
| `--end-date` | `YYYY-MM-DD` (default: yesterday) |
| `--row-limit`, `-n` | Rows per request, max 25000 (default: 1000) |
| `--start-row` | Pagination offset (default: 0) |
| `--all` | Auto-paginate to fetch all results |
| `--aggregation-type` | `auto`, `byPage`, `byProperty`, `byNewsShowcasePanel` |
| `--data-state` | `final` (default) or `all` (include fresh data) |
| `--format`, `-f` | `json`, `table`, `csv` |

### Filter operators

| Operator | Alias | Description |
|----------|-------|-------------|
| `contains` | `~` | Substring match (case-insensitive) |
| `equals` | `=` | Exact match |
| `notContains` | `!~` | Exclude substring |
| `notEquals` | `!=` | Exclude exact match |
| `includingRegex` | `re` | RE2 regex match |
| `excludingRegex` | `!re` | RE2 regex exclude |

## Examples with jq

```bash
# Get top 5 queries by clicks
gsc query -s sc-domain:example.com -d query | jq '.data[:5][] | {query, clicks}'

# Total clicks for a date range
gsc query -s sc-domain:example.com --start-date 2026-01-01 --end-date 2026-03-31 | jq '.data[0].clicks'

# Pages with position > 10 (page 2+)
gsc query -s sc-domain:example.com -d page -n 25000 | jq '[.data[] | select(.position > 10)]'
```

## License

MIT
