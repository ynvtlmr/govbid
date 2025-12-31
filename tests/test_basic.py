"""Tests for the govbid package."""

import pytest
from pydantic import ValidationError

from govbid import (
    GovBidError,
    OpportunityResponse,
    SamApiError,
    SamApiMaxRetriesError,
    SamApiRateLimitError,
    SamOpportunitiesClient,
    SearchResponse,
    settings,
)
from govbid.config import Settings


class TestPackageImports:
    """Test that package exports are available."""

    def test_client_import(self) -> None:
        """Test that SamOpportunitiesClient is importable."""
        assert SamOpportunitiesClient is not None

    def test_model_imports(self) -> None:
        """Test that models are importable."""
        assert OpportunityResponse is not None
        assert SearchResponse is not None

    def test_exception_imports(self) -> None:
        """Test that exceptions are importable."""
        assert GovBidError is not None
        assert SamApiError is not None
        assert SamApiRateLimitError is not None
        assert SamApiMaxRetriesError is not None

    def test_settings_import(self) -> None:
        """Test that settings is importable."""
        assert settings is not None


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_sam_api_error_is_govbid_error(self) -> None:
        """SamApiError should be a subclass of GovBidError."""
        assert issubclass(SamApiError, GovBidError)

    def test_rate_limit_error_is_sam_api_error(self) -> None:
        """SamApiRateLimitError should be a subclass of SamApiError."""
        assert issubclass(SamApiRateLimitError, SamApiError)

    def test_max_retries_error_is_sam_api_error(self) -> None:
        """SamApiMaxRetriesError should be a subclass of SamApiError."""
        assert issubclass(SamApiMaxRetriesError, SamApiError)

    def test_can_catch_all_with_base(self) -> None:
        """All custom exceptions should be catchable with GovBidError."""
        with pytest.raises(GovBidError):
            raise SamApiRateLimitError("test")

        with pytest.raises(GovBidError):
            raise SamApiMaxRetriesError("test")


class TestSettings:
    """Test configuration settings."""

    def test_target_naics_configured(self) -> None:
        """Target NAICS codes should be configured."""
        assert settings.TARGET_NAICS is not None
        assert len(settings.TARGET_NAICS) > 0
        assert "541511" in settings.TARGET_NAICS

    def test_target_pscs_configured(self) -> None:
        """Target PSC codes should be configured."""
        assert settings.TARGET_PSCS is not None
        assert len(settings.TARGET_PSCS) > 0

    def test_sam_base_url_configured(self) -> None:
        """SAM base URL should be configured."""
        assert settings.SAM_BASE_URL is not None
        assert "api.sam.gov" in settings.SAM_BASE_URL

    def test_missing_sam_api_key_fails_validation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing SAM_API_KEY should fail validation."""
        # Remove SAM_API_KEY from environment completely
        monkeypatch.delenv("SAM_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            # Create a new Settings instance without SAM_API_KEY
            # _env_file=None prevents loading from .env file
            Settings(_env_file=None)  # type: ignore[call-arg]
