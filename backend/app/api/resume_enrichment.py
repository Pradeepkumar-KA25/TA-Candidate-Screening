from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import (
    get_resume_enrichment_service,
    require_roles,
    get_current_recruiter,
)
from app.models.user import User
from app.schemas.resume_enrichment import (
    ApproveCandidateChangesRequest,
    CandidateReviewListResponse,
    CandidateReviewResponse,
    CreateReviewBatchRequest,
    ProposedFieldChangeResponse,
    RejectCandidateChangesRequest,
    ReviewBatchDetailResponse,
    ReviewBatchListResponse,
    ReviewBatchResponse,
)
from app.services.resume_enrichment_service import ResumeEnrichmentService

router = APIRouter(prefix="/resume-enrichment", tags=["resume-enrichment"])


@router.post(
    "/batches",
    response_model=ReviewBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new review batch",
    description="Create a new batch of candidates for resume enrichment review. Requires Recruiter or Admin role.",
)
def create_review_batch(
    request: CreateReviewBatchRequest,
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
) -> ReviewBatchResponse:
    """
    Create a new review batch.

    This endpoint will:
    1. Select up to batch_size unreviewed candidates
    2. Extract resume data for each candidate
    3. Compare with Zoho data
    4. Create proposed field changes

    Args:
        request: CreateReviewBatchRequest with optional batch_size

    Returns:
        ReviewBatchResponse with batch details and status

    Raises:
        HTTPException: If batch creation fails
    """
    try:
        batch = service.create_review_batch(
            batch_size=request.batch_size, created_by_user_id=current_user.id
        )
        return ReviewBatchResponse.model_validate(batch)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review batch: {str(exc)}",
        ) from exc


@router.get(
    "/batches",
    response_model=ReviewBatchListResponse,
    summary="List review batches",
    description="Get paginated list of all review batches.",
)
def list_review_batches(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
) -> ReviewBatchListResponse:
    """
    Get paginated list of review batches.

    Args:
        page: Page number (1-indexed)
        page_size: Results per page (1-100)

    Returns:
        ReviewBatchListResponse with list of batches and pagination info
    """
    batches, total = service.review_batch_repository.get_paginated(page, page_size)
    return ReviewBatchListResponse(
        batches=[ReviewBatchResponse.model_validate(batch) for batch in batches],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/batches/{batch_id}",
    response_model=ReviewBatchDetailResponse,
    summary="Get batch details",
    description="Get a specific review batch with all candidate reviews and proposed changes.",
)
def get_review_batch_detail(
    batch_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
) -> ReviewBatchDetailResponse:
    """
    Get batch details with paginated candidate reviews.

    Args:
        batch_id: UUID of the batch
        page: Page number for candidates (1-indexed)
        page_size: Results per page

    Returns:
        ReviewBatchDetailResponse with batch info and candidate list

    Raises:
        HTTPException: If batch not found
    """
    batch = service.get_review_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review batch {batch_id} not found",
        )

    # Get candidates for this batch
    candidates, total = service.candidate_review_repository.get_by_batch_id_paginated(batch_id, page, page_size)

    candidate_responses = []
    for candidate_review in candidates:
        # Get proposed changes for this candidate
        proposed_changes = service.proposed_field_change_repository.get_by_candidate_review_id(candidate_review.id)
        candidate_responses.append(
            CandidateReviewResponse(
                **candidate_review.__dict__,
                proposed_changes=[
                    ProposedFieldChangeResponse.model_validate(change) for change in proposed_changes
                ],
            )
        )

    response = ReviewBatchDetailResponse.model_validate(batch)
    response.candidates = candidate_responses
    return response


@router.delete(
    "/batches/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a batch",
    description="Delete a review batch and all related candidate reviews and proposed changes.",
    responses={204: {"description": "Batch successfully deleted"}},
)
def delete_review_batch(
    batch_id: UUID,
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
):
    """
    Delete a review batch and all related records.

    Args:
        batch_id: UUID of the batch to delete

    Returns:
        204 No Content on success

    Raises:
        HTTPException: If batch not found or deletion fails
    """
    try:
        success = service.delete_review_batch(batch_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review batch {batch_id} not found",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete review batch: {str(exc)}",
        ) from exc


@router.get(
    "/candidates/{candidate_review_id}",
    response_model=CandidateReviewResponse,
    summary="Get candidate review details",
    description="Get a specific candidate review with all proposed field changes.",
)
def get_candidate_review_details(
    candidate_review_id: UUID,
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
) -> CandidateReviewResponse:
    """
    Get candidate review details with all proposed changes.

    Args:
        candidate_review_id: UUID of the candidate review

    Returns:
        CandidateReviewResponse with review details and proposed changes

    Raises:
        HTTPException: If candidate review not found
    """
    candidate_review = service.get_candidate_review(candidate_review_id)
    if not candidate_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate review {candidate_review_id} not found",
        )

    proposed_changes = service.proposed_field_change_repository.get_by_candidate_review_id(candidate_review_id)

    return CandidateReviewResponse(
        **candidate_review.__dict__,
        proposed_changes=[ProposedFieldChangeResponse.model_validate(change) for change in proposed_changes],
    )


@router.patch(
    "/candidates/{candidate_review_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve proposed changes",
    description="Approve proposed changes for a candidate (all or specific fields).",
)
def approve_candidate_changes(
    candidate_review_id: UUID,
    request: ApproveCandidateChangesRequest,
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
) -> dict[str, str]:
    """
    Approve proposed changes for a candidate.

    Args:
        candidate_review_id: UUID of the candidate review
        request: ApproveCandidateChangesRequest with optional field_ids

    Returns:
        Dict with success message

    Raises:
        HTTPException: If candidate review not found
    """
    candidate_review = service.get_candidate_review(candidate_review_id)
    if not candidate_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate review {candidate_review_id} not found",
        )

    try:
        count = service.approve_proposed_changes(
            candidate_review_id=candidate_review_id,
            field_ids=request.field_ids,
            user_id=current_user.id,
            notes=request.notes,
        )
        return {"message": f"Successfully approved {count} proposed changes"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve changes: {str(exc)}",
        ) from exc


@router.patch(
    "/candidates/{candidate_review_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject proposed changes",
    description="Reject proposed changes for a candidate (all or specific fields).",
)
def reject_candidate_changes(
    candidate_review_id: UUID,
    request: RejectCandidateChangesRequest,
    service: ResumeEnrichmentService = Depends(get_resume_enrichment_service),
    current_user: User = Depends(require_roles("Recruiter", "Admin")),
) -> dict[str, str]:
    """
    Reject proposed changes for a candidate.

    Args:
        candidate_review_id: UUID of the candidate review
        request: RejectCandidateChangesRequest with optional field_ids

    Returns:
        Dict with success message

    Raises:
        HTTPException: If candidate review not found
    """
    candidate_review = service.get_candidate_review(candidate_review_id)
    if not candidate_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate review {candidate_review_id} not found",
        )

    try:
        count = service.reject_proposed_changes(
            candidate_review_id=candidate_review_id,
            field_ids=request.field_ids,
            user_id=current_user.id,
            notes=request.notes,
        )
        return {"message": f"Successfully rejected {count} proposed changes"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject changes: {str(exc)}",
        ) from exc
