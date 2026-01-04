# Food-Finder

Lead generation tool for finding medium-sized food/ag companies (5-50 employees) that are using basic tools and don't have sophisticated CRM systems.

## Features

- **USDA Organic API** - Bulk download of 76k+ certified organic operations with ~50% contact coverage
- **Contact Extraction** - Extracts emails and phone numbers from websites
- **Tech Detection** - Detects CRM systems to disqualify enterprise companies
- **Lead Scoring** - Scores leads based on contact availability and company signals
- **CSV Export** - Exports qualified leads for email, LinkedIn, or multi-channel outreach

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database and import all USDA leads (76k+)
python main.py scrape

# Score all leads
python main.py score

# View stats
python main.py stats

# Export top leads
python main.py export --format email --min-score 25
```

## Database

The lead database (`leads.db`) is **not committed to git** - it must be regenerated locally.

### Generate the database

```bash
# Full import - downloads USDA bulk data and imports all 76k+ leads
python main.py scrape

# Or filter by state
python main.py scrape --states CA,TX,NY

# Score the leads
python main.py score
```

The USDA bulk download (22MB) is cached at `/tmp/usda_data/stream` for 24 hours.

### Backup your database

If you want to preserve your current database:

```bash
cp leads.db leads.db.backup
```

## Data Sources

| Source | Leads | Contact Coverage | Status |
|--------|-------|------------------|--------|
| `usda_api` | 76,824 | ~50% email/phone | ✅ Recommended |
| `usda_organic` | - | - | ❌ Broken (JS site) |
| `cdph_organic` | 2,800 | 0% (name/city only) | ⚠️ Limited |

```bash
# View available sources
python main.py sources

# Use specific source
python main.py scrape --source usda_api --states CA
```

## Commands

### Scraping

```bash
# Scrape all US states (default: usda_api)
python main.py scrape

# Scrape specific states
python main.py scrape --states CA,TX,NY

# Limit number of leads
python main.py scrape --states VT --max 1000
```

### Scoring

```bash
# Score unscored leads
python main.py score

# Re-score all leads
python main.py score --force
```

### Viewing Leads

```bash
# Database statistics
python main.py stats

# Top leads by score
python main.py top --limit 20

# Search for specific companies
python main.py search "organic farms" --state CA
```

### Exporting

```bash
# Export all qualified leads
python main.py export

# Export for email outreach (leads with emails, score >= 25)
python main.py export --format email --min-score 25

# Export for LinkedIn outreach
python main.py export --format linkedin

# Custom output path
python main.py export -o my_leads.csv --limit 500
```

### Enrichment (Optional)

Enrichment finds websites and extracts additional contact info:

```bash
# Enrich leads that don't have websites
python main.py enrich --max 100
```

## Lead Scoring

Leads are scored based on:

| Signal | Points |
|--------|--------|
| 5-50 employees | +20 |
| Email found | +15 |
| Phone found | +10 |
| No CRM detected | +10 |
| Has job postings | +10 |
| Has website | +5 |
| Basic website (no SPA) | +5 |

**Disqualified if:**
- Has CRM system (HubSpot, Salesforce, etc.)
- 50+ employees

### Score Distribution (typical)

| Score | Meaning | Typical Count |
|-------|---------|---------------|
| 30-35 | Email + Phone + Website | ~8k |
| 25 | Email + Phone OR Email + Website | ~26k |
| 10-20 | Single contact method | ~9k |
| 0 | No contact info | ~34k |

## Project Structure

```
food-finder-pipeline/
├── main.py                 # CLI entry point
├── config.py               # Configuration & API keys
├── requirements.txt        # Dependencies
├── scrapers/
│   ├── usda_api.py         # USDA bulk API scraper (recommended)
│   ├── usda_organic.py     # USDA web scraper (broken)
│   ├── ca_processors.py    # CA CDPH loader
│   └── google_search.py    # Website finder
├── enrichers/
│   ├── contact_extractor.py  # Email/phone extraction
│   └── tech_detector.py      # CRM detection
├── pipeline/
│   ├── orchestrator.py     # Pipeline coordination
│   └── scorer.py           # Lead scoring
├── storage/
│   ├── database.py         # SQLite connection
│   └── models.py           # SQLAlchemy models
└── export/
    └── csv_export.py       # CSV export utilities
```

## Configuration

Key settings in `config.py`:

```python
# Toggle data sources
ENABLED_SOURCES = {
    "usda_api": True,       # Recommended
    "usda_organic": False,  # Broken
    "cdph_organic": False,  # Limited data
}

# Scoring weights
SCORING = {
    "email_found": 15,
    "phone_found": 10,
    "has_website": 5,
    ...
}
```
