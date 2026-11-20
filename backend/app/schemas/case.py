from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.case import CaseStatus, CasePriority, CaseCategory


class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: CaseCategory = CaseCategory.OTHER
    priority: CasePriority = CasePriority.MEDIUM
    investigator_id: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CaseCategory] = None
    priority: Optional[CasePriority] = None
    status: Optional[CaseStatus] = None
    investigator_id: Optional[str] = None


class CaseOut(BaseModel):
    id: str
    case_number: str
    title: str
    description: Optional[str]
    category: CaseCategory
    priority: CasePriority
    status: CaseStatus
    investigator_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: List[CaseOut]
    total: int
    page: int
    per_page: int
