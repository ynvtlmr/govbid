# GovBid

[![CI](https://github.com/yaniv/govbid/actions/workflows/ci.yml/badge.svg)](https://github.com/yaniv/govbid/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Automated pipeline for discovering, analyzing, and drafting proposals for government software contracts using AI.

## Overview

GovBid is a local desktop automation system that autonomously discovers, analyzes, and drafts proposals for government software contracts. The goal is to reduce manual search time by 95% by using AI to filter out irrelevant bids and draft initial technical proposals for valid software opportunities.

### Current Features

- **SAM.gov API Client**: Search federal contract opportunities with rate limiting and retry logic
- **NAICS/PSC Filtering**: Target custom software development contracts (NAICS 541511, 541512, 541519)
- **Async Architecture**: Efficient async HTTP client with proper resource management

### Planned Features

- SQLite database with SQLModel for bid tracking
- RSS feed harvester for CanadaBuys and other sources
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

| Variable       | Description           | Default                |
| -------------- | --------------------- | ---------------------- |
| `SAM_API_KEY`  | Your SAM.gov API key  | Required               |
| `TARGET_NAICS` | NAICS codes to filter | `541511,541512,541519` |
| `TARGET_PSCS`  | PSC codes to filter   | `DA01,DA10`            |
| `SAM_BASE_URL` | SAM.gov API endpoint  | Production URL         |

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
│   ├── config.py        # Configuration via pydantic-settings
│   ├── exceptions.py    # Custom exception hierarchy
│   ├── main.py          # CLI entry point
│   ├── models.py        # Pydantic models for API responses
│   └── sam_client.py    # SAM.gov API client
├── tests/
│   ├── test_basic.py    # Basic tests
│   └── test_models.py   # Model validation tests
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
