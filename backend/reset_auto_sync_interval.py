#!/usr/bin/env python3
"""Quick script to reset auto_sync_interval_minutes back to 5"""

from app.core.database import get_engine
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    engine = get_engine()
    with Session(engine) as session:
        # Update all integration_settings records to 5-minute interval
        result = session.execute(
            text("UPDATE integration_settings SET auto_sync_interval_minutes = 5")
        )
        session.commit()
        print(f"✅ Updated {result.rowcount} record(s)")
        print(f"Auto sync interval reset to 5 minutes")
        
        # Verify the change
        verify = session.execute(
            text("SELECT id, auto_sync_interval_minutes, last_auto_sync_at FROM integration_settings")
        )
        rows = verify.fetchall()
        print(f"\nCurrent settings:")
        for row in rows:
            print(f"  ID: {row[0]}, Interval: {row[1]} mins, Last sync: {row[2]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
