#!/usr/bin/env python
"""Update Zoho OAuth credentials in database."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.core.crypto import encrypt_value
from app.models.integration_settings import IntegrationSettings

def update_credentials():
    """Update Zoho OAuth credentials."""
    
    # New credentials from Zoho admin
    new_client_id = "1000.WA5TEPHE77PLKH4QFWL1NV044OCK7P"
    new_client_secret = "50686efc31975c713dc65004087e17ee56a7e802e7"
    new_access_token = "1000.0287eee2d7787850a27791b6b811bc20.f23fba24c17c53aee04e3ac7ee4f958a"
    new_refresh_token = "1000.016538f89cf868d52ec10a5b687e5754.938160967bfaf48393a18f82bb3c659c"
    
    print("=" * 70)
    print("UPDATING ZOHO OAUTH CREDENTIALS")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get existing integration
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[ERROR] No Zoho integration found in database")
                return False
            
            # Update credentials
            print("[INFO] Updating credentials...")
            integration.client_id = new_client_id
            integration.client_secret = new_client_secret
            integration.access_token_encrypted = encrypt_value(new_access_token)
            integration.refresh_token_encrypted = encrypt_value(new_refresh_token)
            integration.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            
            print("[OK] Credentials updated successfully")
            print()
            print("New Credentials Summary:")
            print("-" * 70)
            print("Client ID: " + new_client_id[:20] + "...")
            print("Client Secret: " + new_client_secret[:20] + "...")
            print("Access Token: " + new_access_token[:30] + "...")
            print("Refresh Token: " + new_refresh_token[:30] + "...")
            print()
            print("[OK] Credentials encrypted and stored in database")
            return True
            
    except Exception as e:
        print("[ERROR] Failed to update credentials: " + str(e))
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = update_credentials()
    sys.exit(0 if success else 1)
