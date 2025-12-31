"""Configuration settings for GovBid."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    SAM_API_KEY: str

    # Target NAICS Codes
    # 541511: Custom Computer Programming Services
    # 541512: Computer Systems Design Services
    # 541519: Other Computer Related Services
    TARGET_NAICS: List[str] = ["541511", "541512", "541519"]

    # Target PSC Codes
    # DA01: IT/Telecom - Business App/Application Development Support (Labor)
    # DA10: IT/Telecom - Business App/Application Development SaaS
    TARGET_PSCS: List[str] = ["DA01", "DA10"]

    # SAM API Base URL (production endpoint)
    SAM_BASE_URL: str = "https://api.sam.gov/prod/opportunities/v2/search"

    # Canada Buys Settings
    CANADA_BUYS_CSV_URL: str = "https://canadabuys.canada.ca/opendata/pub/newTenderNotice-nouvelAvisAppelOffres.csv"
    # Target UNSPSC Codes (starting with)
    # 8111: Computer services
    TARGET_UNSPSC_PREFIXES: List[str] = ["8111"]

    # CSV Archiving
    RAW_DATA_DIR: str = "data/canada_buys_raw"

    # SAM.gov Archiving & History
    SAM_RAW_DATA_DIR: str = "data/sam_gov_raw"
    SAM_HISTORY_FILE: str = "data/sam_history.jsonl"

    RETENTION_DAYS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
