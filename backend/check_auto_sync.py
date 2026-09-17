#!/usr/bin/env python3
"""Check auto-sync status and recent syncs"""

from app.core.database import get_engine
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

engine = get_engine()
inspector = inspect(engine)

print("=== SYNC LOGS TABLE SCHEMA ===")
columns = inspector.get_columns('sync_logs')
for col in columns:
    print(f"  - {col['name']}: {col['type']}")

print("\n=== AUTO-SYNC SETTINGS ===")
with Session(engine) as session:
    result = session.execute(text('SELECT auto_sync_enabled, auto_sync_interval_minutes, last_auto_sync_at FROM integration_settings LIMIT 1'))
    row = result.fetchone()
    if row:
        print(f"  Enabled: {row[0]}")
        print(f"  Interval: {row[1]} minutes")
        print(f"  Last auto-sync at: {row[2]}")

print("\n=== RECENT SYNC LOGS ===")
with Session(engine) as session:
    sync_logs = session.execute(text('SELECT id, status, triggered_by, started_at FROM sync_logs ORDER BY started_at DESC LIMIT 5'))
    rows = sync_logs.fetchall()
    if rows:
        print(f"  Found {len(rows)} recent syncs:")
        for r in rows:
            print(f"    - ID: {r[0]}, Status: {r[1]}, Triggered by: {r[2]}, Started: {r[3]}")
    else:
        print("  No sync logs found")

print("\n=== CANDIDATE COUNT ===")
with Session(engine) as session:
    count = session.execute(text('SELECT COUNT(*) FROM candidates'))
    print(f"  Total candidates in DB: {count.scalar()}")
