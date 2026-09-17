#!/usr/bin/env python3
"""Fix stuck sync and clear running state"""

from app.core.database import get_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, UTC

engine = get_engine()
with Session(engine) as session:
    print("=== CLEARING STUCK SYNC ===")
    
    # Mark the stuck sync as failed
    result = session.execute(text('''
        UPDATE sync_logs 
        SET status = 'failed', 
            error_message = 'Auto-recovered from stuck state',
            completed_at = :now
        WHERE status = 'running'
    '''), {'now': datetime.now(UTC)})
    session.commit()
    
    print(f"✅ Updated {result.rowcount} stuck sync(s)")
    
    # Verify
    count_query = session.execute(text("SELECT COUNT(*) FROM sync_logs WHERE status = 'running'"))
    running_count = count_query.scalar()
    print(f"Syncs still in 'running' state: {running_count}")
    
    print("\n=== AUTO-SYNC READY ===")
    print("✅ Auto-sync can now proceed with next scheduled sync")
