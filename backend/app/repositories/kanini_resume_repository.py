"""
Kanini Resume Repository - Database operations
"""

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.kanini_resume_db import (
    KaniniResume,
    KaniniUserTemplate,
)


class KaniniResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        filename: str,
        parsed_data: dict,
    ) -> KaniniResume:
        resume = KaniniResume(
            user_id=user_id,
            filename=filename,
            parsed_data=parsed_data,
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_id(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[KaniniResume]:
        return self.db.query(KaniniResume).filter(
            KaniniResume.id == resume_id,
            KaniniResume.user_id == user_id,
        ).first()

    def list_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[KaniniResume]:
        return self.db.query(KaniniResume).filter(
            KaniniResume.user_id == user_id
        ).offset(skip).limit(limit).all()

    def update(self, resume_id: uuid.UUID, user_id: uuid.UUID, parsed_data: dict) -> Optional[KaniniResume]:
        resume = self.get_by_id(resume_id, user_id)
        if not resume:
            return None
        resume.parsed_data = parsed_data
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def delete(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        resume = self.get_by_id(resume_id, user_id)
        if not resume:
            return False
        self.db.delete(resume)
        self.db.commit()
        return True


class KaniniUserTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        template_name: str,
        description: str,
        template_spec: dict,
    ) -> KaniniUserTemplate:
        template = KaniniUserTemplate(
            user_id=user_id,
            template_name=template_name,
            description=description,
            template_spec=template_spec,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def list_by_user(self, user_id: uuid.UUID) -> List[KaniniUserTemplate]:
        return self.db.query(KaniniUserTemplate).filter(
            KaniniUserTemplate.user_id == user_id
        ).all()

    def get_by_id(self, template_id: uuid.UUID, user_id: uuid.UUID) -> Optional[KaniniUserTemplate]:
        return self.db.query(KaniniUserTemplate).filter(
            KaniniUserTemplate.id == template_id,
            KaniniUserTemplate.user_id == user_id,
        ).first()

    def update(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        template_name: str,
        description: str,
        template_spec: dict,
    ) -> Optional[KaniniUserTemplate]:
        template = self.get_by_id(template_id, user_id)
        if not template:
            return None
        template.template_name = template_name
        template.description = description
        template.template_spec = template_spec
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        template = self.get_by_id(template_id, user_id)
        if not template:
            return False
        self.db.delete(template)
        self.db.commit()
        return True
