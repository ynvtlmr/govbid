"""GovBid CLI entry point for testing API connectivity."""

import asyncio
import logging
from datetime import date, timedelta

from .config import settings
from .sam_client import SamOpportunitiesClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_search() -> None:
    """Run a sample search to verify SAM.gov API connectivity."""
    logger.info("Starting SAM.gov opportunity search...")
    logger.info(f"Target NAICS codes: {settings.TARGET_NAICS}")
    logger.info(f"Target PSC codes: {settings.TARGET_PSCS}")

    async with SamOpportunitiesClient() as client:
        today = date.today()
        posted_from = today - timedelta(days=30)

        logger.info(f"Searching opportunities from {posted_from} to {today}...")

        opportunities = await client.search_opportunities(
            posted_from=posted_from,
            posted_to=today,
            naics=settings.TARGET_NAICS,
            pscs=settings.TARGET_PSCS,
        )

        logger.info(f"Found {len(opportunities)} unique opportunities")

        if opportunities:
            logger.info("Sample opportunities:")
            for opp in opportunities[:5]:
                logger.info(f"  - [{opp.noticeId}] {opp.title}")
                if opp.responseDeadLine:
                    logger.info(f"    Deadline: {opp.responseDeadLine}")
        else:
            logger.info("No opportunities found for the specified criteria.")


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_search())
    except KeyboardInterrupt:
        logger.info("Search interrupted by user.")
    except Exception:
        logger.exception("Search failed")
        raise


if __name__ == "__main__":
    main()
