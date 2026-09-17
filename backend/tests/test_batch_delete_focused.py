"""Test batch delete functionality."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.models.candidate import Candidate
from app.models.user import User


def _header(user: User) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_batch_delete(sqlite_session, user_factory) -> None:
    """Test that batch delete actually deletes candidates."""
    admin = user_factory(role="Admin")
    
    # Create test candidates
    now = datetime.now(UTC)
    candidates = [
        Candidate(
            zoho_record_id=f"z-batch-{i}",
            zoho_candidate_id=f"c-batch-{i}",
            full_name=f"Batch Delete Test {i}",
            email=f"batch{i}@test.com",
            current_location="Test City",
            total_experience_years=5.0,
            notice_period_days=30,
            status="Active",
            created_at=now,
            updated_at=now,
        )
        for i in range(3)
    ]
    sqlite_session.add_all(candidates)
    sqlite_session.commit()
    
    # Get IDs before deletion
    candidate_ids = [str(c.id) for c in candidates]
    print(f"\n=== Batch Delete Test ===")
    print(f"Created {len(candidate_ids)} candidates:")
    for cid in candidate_ids:
        print(f"  - {cid}")
    
    # Verify they exist
    verify_stmt = select(Candidate).where(Candidate.id.in_([c.id for c in candidates]))
    existing_before = sqlite_session.scalars(verify_stmt).all()
    print(f"\nVerified {len(existing_before)} candidates exist before deletion")
    assert len(existing_before) == 3, f"Expected 3 candidates, found {len(existing_before)}"
    
    # Setup FastAPI dependency injection
    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    try:
        client = TestClient(app)
        
        # Call batch delete
        print(f"\nCalling /api/v1/candidates/batch/delete with IDs: {candidate_ids}")
        response = client.post(
            "/api/v1/candidates/batch/delete",
            json={"candidate_ids": candidate_ids},
            headers=_header(admin)
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        deleted_count = result.get("deleted_count", 0)
        
        print(f"\nAPI returned: deleted_count={deleted_count}")
        
        # Verify in database
        remaining = sqlite_session.scalars(verify_stmt).all()
        print(f"Database now has {len(remaining)} candidates")
        
        # The actual assertion
        if deleted_count == 0:
            print("\n❌ PROBLEM: API returned deleted_count=0!")
            print("   Candidates may not have been found or deleted.")
            assert deleted_count == 3, f"Expected to delete 3 candidates, but deleted_count={deleted_count}"
        else:
            print(f"\n✅ SUCCESS: Deleted {deleted_count} candidates")
            assert deleted_count == 3, f"Expected to delete 3, deleted {deleted_count}"
            assert len(remaining) == 0, f"Expected 0 remaining, found {len(remaining)}"
        
    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
