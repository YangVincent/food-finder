# Leads Monitoring UI

A web-based dashboard for monitoring and managing scraped leads from the Food Finder lead generation tool.

## Overview

This UI provides real-time monitoring of leads scraped from organic food/agriculture company databases. It consists of:

- **FastAPI Backend** (`api/`) - REST API that connects to the existing SQLite database
- **Next.js Frontend** (`web/`) - React-based dashboard with dark theme

## Features

### Dashboard
- Total leads, qualified count, email/website availability stats
- Enrichment progress bar showing completion percentage
- Score distribution chart (0-20, 21-40, 41-60, 61-80 ranges)
- Quick stats bar with phone count, disqualified count, conversion rate

### Leads Table
- Searchable by company name, city, or email
- Filterable by state, source, and qualification status
- Sortable columns (company, state, score)
- Pagination (50 leads per page)
- Contact icons showing email/phone/website availability

### Lead Detail View
- Full contact information with copy-to-clipboard buttons
- Location details
- Company source and tech stack info
- CRM detection status
- Enrichment timestamps

## Tech Stack

**Backend:**
- FastAPI
- SQLAlchemy (reuses existing `storage/` module)
- Pydantic for response schemas

**Frontend:**
- Next.js 14 (App Router)
- React Query for data fetching
- TailwindCSS for styling
- Recharts for charts
- Lucide React for icons

**Design:**
- Industrial dark theme with warm amber accents
- JetBrains Mono (data/monospace) + Outfit (body) fonts
- Noise texture overlay for depth

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Existing `leads.db` database in the project root

### Install Dependencies

```bash
# API dependencies
cd ui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd web
npm install
```

## Running the App

You need to run both the API and frontend servers:

```bash
# Terminal 1 - Start API server (port 8000)
cd /path/to/food-finder-ui
source ui/venv/bin/activate
uvicorn ui.api.main:app --reload --port 8000

# Terminal 2 - Start frontend server (port 3000)
cd /path/to/food-finder-ui/ui/web
npm run dev
```

Then open http://localhost:3000 in your browser.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stats/overview` | Overall lead statistics |
| `GET /api/stats/score-distribution` | Score distribution by range |
| `GET /api/leads/` | Paginated leads list with filters |
| `GET /api/leads/{id}` | Single lead details |
| `GET /api/leads/filters/` | Available filter options (states, sources) |

### Query Parameters for `/api/leads/`

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50, max: 100)
- `sort_by` - Column to sort (name, score, state, city, created_at)
- `sort_order` - asc or desc
- `state` - Filter by state
- `source` - Filter by data source
- `is_qualified` - Filter by qualification status
- `has_email` - Filter by email presence
- `search` - Search term for name/city/email

## Project Structure

```
ui/
├── api/                      # FastAPI backend
│   ├── main.py              # App entry point, CORS config
│   ├── schemas.py           # Pydantic response models
│   ├── dependencies.py      # Database session dependency
│   └── routes/
│       ├── leads.py         # Leads endpoints
│       └── stats.py         # Statistics endpoints
│
├── web/                      # Next.js frontend
│   ├── app/
│   │   ├── page.tsx         # Dashboard
│   │   └── leads/
│   │       ├── page.tsx     # Leads table
│   │       └── [id]/page.tsx # Lead detail
│   ├── components/          # React components
│   └── lib/
│       ├── api.ts           # API client
│       ├── types.ts         # TypeScript types
│       └── utils.ts         # Utility functions
│
├── venv/                     # Python virtual environment
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Development

### API Development

The API auto-reloads on file changes when using `--reload` flag.

API documentation is available at http://localhost:8000/docs (Swagger UI).

### Frontend Development

The Next.js dev server supports hot module replacement.

To build for production:
```bash
cd ui/web
npm run build
```
