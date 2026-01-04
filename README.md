# Food-Finder

Lead generation tool for finding medium-sized food/ag companies (5-50 employees) that are using basic tools and don't have sophisticated CRM systems.

## Features

- **USDA Organic Database Scraper** - Scrapes certified organic operations nationwide
- **Website Discovery** - Finds company websites via DuckDuckGo search
- **Contact Extraction** - Extracts emails and phone numbers from websites
- **Tech Detection** - Detects CRM systems to disqualify enterprise companies
- **Lead Scoring** - Scores leads based on contact availability and company signals
- **CSV Export** - Exports qualified leads for email, LinkedIn, or multi-channel outreach

## Installation

```bash
cd food-finder

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Initialize the database

```bash
python main.py init
```

### Run the full pipeline

```bash
# Scrape and enrich all states (takes time)
python main.py run

# Scrape specific states
python main.py run --states CA,TX,NY

# Limit the number of leads
python main.py run --states VT --max-scrape 100 --max-enrich 50
```

### Run steps individually

```bash
# Just scrape (no enrichment)
python main.py scrape --states CA,OR,WA --max 500

# Just enrich existing leads
python main.py enrich --max 100
```

### View leads

```bash
# Database statistics
python main.py stats

# Top leads by score
python main.py top --limit 20

# Search for specific companies
python main.py search "organic farms" --state CA
```

### Export leads

```bash
# Export all qualified leads
python main.py export

# Export for email outreach (only leads with emails)
python main.py export --format email --min-score 30

# Export for LinkedIn outreach
python main.py export --format linkedin

# Custom output path
python main.py export -o my_leads.csv --limit 500
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

## Project Structure

```
food-finder/
├── main.py              # CLI entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── scrapers/
│   ├── usda_organic.py  # USDA database scraper
│   └── google_search.py # Website finder
├── enrichers/
│   ├── contact_extractor.py  # Email/phone extraction
│   └── tech_detector.py      # CRM detection
├── pipeline/
│   ├── orchestrator.py  # Pipeline coordination
│   └── scorer.py        # Lead scoring
├── storage/
│   ├── database.py      # SQLite connection
│   └── models.py        # SQLAlchemy models
└── export/
    └── csv_export.py    # CSV export utilities
```

## Data Sources

Currently implemented:
- USDA Organic Integrity Database (40k+ certified operations)

Planned:
- State agriculture department directories
- FDA registered food facilities
- Industry association member lists
