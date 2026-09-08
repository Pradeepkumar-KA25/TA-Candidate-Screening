"""Schemas for shortlist export operations."""

from pydantic import BaseModel


class ExportMetadata(BaseModel):
    """Metadata about an Excel export."""
    
    filename: str
    candidate_count: int
    jd_title: str
    generated_at: str


class ExportResponse(BaseModel):
    """Response for export operations."""
    
    message: str
    metadata: ExportMetadata
