"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from govbid.models import OpportunityResponse, SearchResponse


class TestOpportunityResponse:
    """Tests for OpportunityResponse model."""

    def test_minimal_valid_opportunity(self) -> None:
        """Test creating opportunity with only required fields."""
        opp = OpportunityResponse(
            noticeId="abc123",
            title="Test Opportunity",
        )
        assert opp.noticeId == "abc123"
        assert opp.title == "Test Opportunity"
        assert opp.solicitationNumber is None

    def test_full_opportunity(self) -> None:
        """Test creating opportunity with all fields."""
        opp = OpportunityResponse(
            noticeId="abc123",
            solicitationNumber="SOL-2024-001",
            title="Custom Software Development",
            fullParentPathName="Department of Defense",
            subTier="Army",
            office="Acquisition Office",
            postedDate="2024-01-15",
            type="Solicitation",
            baseType="Combined Synopsis/Solicitation",
            archiveType="auto15",
            archiveDate="2024-03-15",
            typeOfSetAsideDescription="Small Business",
            typeOfSetAside="SBA",
            responseDeadLine="2024-02-15T17:00:00-05:00",
            naicsCode="541511",
            naicsCodes=["541511", "541512"],
            classificationCode="DA01",
            active=True,
            organizationType="OFFICE",
            resourceLinks=["https://example.gov/doc.pdf"],
            uiLink="https://sam.gov/opp/abc123",
            description="Looking for software development services.",
        )
        assert opp.department == "Department of Defense"
        assert opp.naicsCode == "541511"
        assert opp.active is True
        assert len(opp.naicsCodes or []) == 2

    def test_alias_field_population(self) -> None:
        """Test that alias fields work correctly."""
        opp = OpportunityResponse(
            noticeId="abc123",
            title="Test",
            fullParentPathName="Test Department",
        )
        assert opp.department == "Test Department"

    def test_missing_required_field_raises(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            OpportunityResponse(title="Missing noticeId")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            OpportunityResponse(noticeId="Missing title")  # type: ignore[call-arg]


class TestSearchResponse:
    """Tests for SearchResponse model."""

    def test_valid_search_response(self) -> None:
        """Test creating a valid search response."""
        response = SearchResponse(
            totalRecords=2,
            opportunitiesData=[
                OpportunityResponse(noticeId="1", title="Opp 1"),
                OpportunityResponse(noticeId="2", title="Opp 2"),
            ],
        )
        assert response.totalRecords == 2
        assert len(response.opportunitiesData) == 2
        assert response.opportunitiesData[0].noticeId == "1"

    def test_empty_opportunities_list(self) -> None:
        """Test search response with no results."""
        response = SearchResponse(
            totalRecords=0,
            opportunitiesData=[],
        )
        assert response.totalRecords == 0
        assert len(response.opportunitiesData) == 0

    def test_missing_opportunities_raises(self) -> None:
        """Test that missing opportunitiesData raises ValidationError."""
        with pytest.raises(ValidationError):
            SearchResponse(totalRecords=0)  # type: ignore[call-arg]
