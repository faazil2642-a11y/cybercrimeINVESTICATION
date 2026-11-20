from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.models.case import InvestigationCase, CaseStatus, CasePriority, CaseCategory
from app.models.user import User


def generate_case_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(InvestigationCase).count() + 1
    return f"CT-{year}-{count:03d}"


def create_case(
    db: Session,
    title: str,
    description: Optional[str] = None,
    category: CaseCategory = CaseCategory.OTHER,
    priority: CasePriority = CasePriority.MEDIUM,
    investigator_id: Optional[str] = None
) -> InvestigationCase:
    case_num = generate_case_number(db)
    new_case = InvestigationCase(
        case_number=case_num,
        title=title,
        description=description,
        category=category,
        priority=priority,
        status=CaseStatus.ACTIVE,
        investigator_id=investigator_id
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


def get_cases(
    db: Session,
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    investigator_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[InvestigationCase], int]:
    query = db.query(InvestigationCase)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                InvestigationCase.case_number.ilike(search_filter),
                InvestigationCase.title.ilike(search_filter),
                InvestigationCase.description.ilike(search_filter)
            )
        )

    if status:
        try:
            query = query.filter(InvestigationCase.status == CaseStatus(status.upper()))
        except ValueError:
            pass

    if priority:
        try:
            query = query.filter(InvestigationCase.priority == CasePriority(priority.upper()))
        except ValueError:
            pass

    if category:
        try:
            query = query.filter(InvestigationCase.category == CaseCategory(category.upper()))
        except ValueError:
            pass

    if investigator_id:
        query = query.filter(InvestigationCase.investigator_id == investigator_id)

    total = query.count()
    items = query.order_by(desc(InvestigationCase.created_at)).offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_case_by_id(db: Session, case_id: str) -> Optional[InvestigationCase]:
    return db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()


def update_case(
    db: Session,
    case_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[CaseCategory] = None,
    priority: Optional[CasePriority] = None,
    status: Optional[CaseStatus] = None,
    investigator_id: Optional[str] = None
) -> Optional[InvestigationCase]:
    case = get_case_by_id(db, case_id)
    if not case:
        return None

    if title is not None:
        case.title = title
    if description is not None:
        case.description = description
    if category is not None:
        case.category = category
    if priority is not None:
        case.priority = priority
    if status is not None:
        case.status = status
    if investigator_id is not None:
        case.investigator_id = investigator_id

    db.commit()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: str) -> bool:
    case = get_case_by_id(db, case_id)
    if not case:
        return False
    db.delete(case)
    db.commit()
    return True
