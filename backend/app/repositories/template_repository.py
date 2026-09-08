"""
Template Repository - Database operations for custom user templates
"""

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.kanini_resume_db import KaniniUserTemplate


class KaniniUserTemplateRepository:
    """Repository for managing custom user templates"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        name: str,
        description: str,
        template_spec: dict,
    ) -> KaniniUserTemplate:
        """Create a new user template"""
        template = KaniniUserTemplate(
            user_id=user_id,
            template_name=name,
            description=description,
            template_spec=template_spec,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, template_id: uuid.UUID, user_id: uuid.UUID) -> Optional[KaniniUserTemplate]:
        """Get a specific template by ID"""
        return self.db.query(KaniniUserTemplate).filter(
            KaniniUserTemplate.id == template_id,
            KaniniUserTemplate.user_id == user_id,
        ).first()

    def list_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[KaniniUserTemplate]:
        """List all templates for a user"""
        return self.db.query(KaniniUserTemplate).filter(
            KaniniUserTemplate.user_id == user_id
        ).offset(skip).limit(limit).all()

    def update(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template_spec: Optional[dict] = None,
    ) -> Optional[KaniniUserTemplate]:
        """Update a template"""
        template = self.get_by_id(template_id, user_id)
        if not template:
            return None

        if name is not None:
            template.template_name = name
        if description is not None:
            template.description = description
        if template_spec is not None:
            template.template_spec = template_spec

        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a template"""
        template = self.get_by_id(template_id, user_id)
        if not template:
            return False

        self.db.delete(template)
        self.db.commit()
        return True
