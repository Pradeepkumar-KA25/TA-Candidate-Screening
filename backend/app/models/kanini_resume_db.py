"""
Kanini Resume Database Models (SQLAlchemy)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class KaniniResume(Base):
    """Uploaded resume with parsed data"""
    __tablename__ = "kanini_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    parsed_data = Column(JSON, nullable=True)
    extraction_status = Column(String(32), nullable=False, default="completed", index=True)
    extraction_progress = Column(Integer, nullable=False, default=100)
    extraction_error = Column(Text, nullable=True)
    extraction_model = Column(String(255), nullable=True)
    source_reference = Column(Text, nullable=True)
    source_file_type = Column(String(16), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class KaniniUserTemplate(Base):
    """Custom user-created templates"""
    __tablename__ = "kanini_user_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_spec = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])

