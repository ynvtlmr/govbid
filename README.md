# GovBid

[![CI](https://github.com/yaniv/govbid/actions/workflows/ci.yml/badge.svg)](https://github.com/yaniv/govbid/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Automated pipeline for discovering, analyzing, and drafting proposals for government software contracts using AI.

## Overview

GovBid is a local desktop automation system that autonomously discovers, analyzes, and drafts proposals for government software contracts. The goal is to reduce manual search time by 95% by using AI to filter out irrelevant bids and draft initial technical proposals for valid software opportunities.

### Current Features

- **SAM.gov API Client**: Search federal contract opportunities with rate limiting and retry logic
- **Canada Buys Harvester**: Fetch and filter Canadian government tenders from CSV feed
- **NAICS/PSC Filtering**: Target custom software development contracts (NAICS 541511, 541512, 541519)
- **UNSPSC Filtering**: Target software services (Computer services 8111\*)
- **Async Architecture**: Efficient async HTTP client with proper resource management
- **History Tracking**: Deduplication via persistent JSONL history file

### Planned Features

- SQLite database with SQLModel for bid tracking
- RSS feed harvester for additional sources
- Gemini AI integration for bid relevance scoring
- Streamlit dashboard for bid management
- Automated proposal drafting

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yaniv/govbid.git
   cd govbid
   ```

2. Install dependencies:

   ```bash
   uv sync --dev
   ```

3. Create a `.env` file with your SAM.gov API key:

   ```bash
   SAM_API_KEY=your_api_key_here
   ```

   Get your API key from [SAM.gov](https://sam.gov/content/entity-registration).

## Usage

### Run a Sample Search

```bash
uv run python -m govbid.main
```

This will search for software development opportunities posted in the last 30 days.

### Use as a Library

```python
import asyncio
from datetime import date, timedelta
from govbid import SamOpportunitiesClient

async def search():
    async with SamOpportunitiesClient() as client:
        opportunities = await client.search_opportunities(
            posted_from=date.today() - timedelta(days=30),
            posted_to=date.today(),
            naics=["541511"],  # Custom Computer Programming
        )
        for opp in opportunities:
            print(f"{opp.title} - Deadline: {opp.responseDeadLine}")

asyncio.run(search())
```

## Configuration

Configuration is managed via environment variables (loaded from `.env`):

| Variable                 | Description                        | Default                    |
| ------------------------ | ---------------------------------- | -------------------------- |
| `SAM_API_KEY`            | Your SAM.gov API key               | Required                   |
| `TARGET_NAICS`           | NAICS codes to filter              | `541511,541512,541519`     |
| `TARGET_PSCS`            | PSC codes to filter                | `DA01,DA10`                |
| `SAM_BASE_URL`           | SAM.gov API endpoint               | Production URL             |
| `CANADA_BUYS_CSV_URL`    | Canada Buys CSV feed URL           | Production URL             |
| `TARGET_UNSPSC_PREFIXES` | UNSPSC code prefixes to filter     | `8111` (Computer services) |
| `RAW_DATA_DIR`           | Canada Buys archive directory      | `data/canada_buys_raw`     |
| `SAM_RAW_DATA_DIR`       | SAM.gov JSON archive directory     | `data/sam_gov_raw`         |
| `SAM_HISTORY_FILE`       | Path to deduplication history file | `data/sam_history.jsonl`   |
| `RETENTION_DAYS`         | Days to retain archived data       | `60`                       |

## Development

### Running Tests

```bash
uv run pytest -v
```

### Running Linters

```bash
# Lint check
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check
uv run ty check
```

### Pre-commit Hooks

Install pre-commit hooks for automatic linting:

```bash
uv run pre-commit install
```

## Project Structure

```
govbid/
├── src/govbid/
│   ├── __init__.py      # Package exports
│   ├── canada_buys.py   # Canada Buys CSV harvester
│   ├── config.py        # Configuration via pydantic-settings
│   ├── exceptions.py    # Custom exception hierarchy
│   ├── history.py       # Deduplication history manager
│   ├── main.py          # CLI entry point
│   ├── models.py        # Pydantic models for API responses
│   └── sam_client.py    # SAM.gov API client
├── tests/
│   ├── test_basic.py       # Basic package tests
│   ├── test_canada_buys.py # Canada Buys harvester tests
│   ├── test_models.py      # Model validation tests
│   └── test_sam_history.py # History manager tests
├── docs/
│   ├── project_outline.md
│   ├── project_plan.md
│   ├── SAM/             # SAM.gov API documentation
│   └── CanadaBuys/      # CanadaBuys API documentation
├── pyproject.toml       # Project configuration
└── README.md
```

## Rate Limiting

The SAM.gov API has rate limits. This client implements:

- Sequential requests via semaphore (1 concurrent request)
- Random delay of 2-4 seconds between requests
- Exponential backoff retry for 429 errors
- Retry-After header parsing

**Note**: Too many concurrent requests or rapid sequential calls can trigger a 429 error that blocks your API key for 24 hours.

## License

MIT License - See LICENSE file for details.
