"""Pydantic models for SAM.gov API responses."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OpportunityResponse(BaseModel):
    """SAM.gov opportunity data from search API response."""

    model_config = ConfigDict(populate_by_name=True)

    noticeId: str
    solicitationNumber: Optional[str] = None
    title: str
    department: Optional[str] = Field(None, alias="fullParentPathName")
    subTier: Optional[str] = Field(None, alias="subTier")
    office: Optional[str] = Field(None, alias="office")
    postedDate: Optional[str] = None
    type: Optional[str] = None
    baseType: Optional[str] = None
    archiveType: Optional[str] = None
    archiveDate: Optional[str] = None
    typeOfSetAsideDescription: Optional[str] = None
    typeOfSetAside: Optional[str] = None
    responseDeadLine: Optional[str] = None
    naicsCode: Optional[str] = None
    naicsCodes: Optional[List[str]] = None
    classificationCode: Optional[str] = None
    active: Optional[bool] = None
    organizationType: Optional[str] = None
    resourceLinks: Optional[List[str]] = None
    uiLink: Optional[str] = None
    description: Optional[str] = None


class SearchResponse(BaseModel):
    """SAM.gov search API response wrapper."""

    totalRecords: int
    opportunitiesData: List[OpportunityResponse]
