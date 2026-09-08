#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')
from sqlalchemy import text, inspect
from app.core.database import get_engine

try:
    engine = get_engine()
    insp = inspect(engine)
    tables = sorted(insp.get_table_names())
    print("Tables in database:")
    for table in tables:
        print(f"  - {table}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
