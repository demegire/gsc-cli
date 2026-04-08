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
