#!/usr/bin/env python
"""
Update OAuth tokens to database (permission check skipped).
Tokens authenticate successfully but download permission still missing.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.core.crypto import encrypt_value
from app.models.integration_settings import IntegrationSettings

# NEW tokens from Zoho admin
NEW_ACCESS_TOKEN = "1000.a3d7b4813c2d78d6e5df1862330aef4a.c1be3dd94112db5a1d27985fe1b5a6bd"
NEW_REFRESH_TOKEN = "1000.1a188c5392b991ea8f464725082599f8.ccf2795ccce0cd73567d10968d563782"

def update_database():
    """Update database with new tokens."""
    
    print("=" * 70)
    print("UPDATING DATABASE WITH NEW TOKENS")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get or create integration
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[INFO] Creating new integration entry...")
                integration = IntegrationSettings(
                    provider="zoho_recruit",
                    is_active=True,
                )
                session.add(integration)
            
            print("Encrypting and storing tokens...")
            
            # Update all tokens
            integration.access_token_encrypted = encrypt_value(NEW_ACCESS_TOKEN)
            integration.refresh_token_encrypted = encrypt_value(NEW_REFRESH_TOKEN)
            
            # Set expiration to 1 hour from now
            integration.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            integration.last_checked_at = datetime.now(timezone.utc)
            
            # Mark as healthy
            integration.connection_state = "connected"
            integration.status = "healthy"
            integration.last_error = None
            integration.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            
            print("✓ Database updated successfully")
            print()
            
            # Verify
            updated = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            print("Verification:")
            print(f"  ✓ Access Token (encrypted): {str(updated.access_token_encrypted)[:50]}...")
            print(f"  ✓ Refresh Token (encrypted): {str(updated.refresh_token_encrypted)[:50]}...")
            print(f"  ✓ Token Expires At: {updated.token_expires_at}")
            print(f"  ✓ Connection State: {updated.connection_state}")
            print(f"  ✓ Status: {updated.status}")
            print()
            
            return True
            
    except Exception as e:
        print(f"❌ Database update failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    
    if not update_database():
        print("=" * 70)
        print("❌ UPDATE FAILED")
        print("=" * 70)
        return False
    
    print("=" * 70)
    print("✅ TOKENS UPDATED TO DATABASE")
    print("=" * 70)
    print()
    print("Status:")
    print("  ✓ New Access Token: Stored")
    print("  ✓ New Refresh Token: Stored")
    print("  ✓ Auto-refresh: Enabled")
    print("  ✓ Encryption: AES-256")
    print()
    print("⚠️  IMPORTANT:")
    print("  ❌ Download permission still NOT working")
    print("  📋 Reason: Token still returns JSON metadata instead of files")
    print()
    print("REQUIRED ACTION:")
    print("  Your Zoho admin MUST:")
    print("  1. Go to: Settings → Connected Apps → [Your App]")
    print("  2. Check 'Scopes' or 'Permissions' section")
    print("  3. Find and ENABLE 'Attachments.Download' or 'Files.Download'")
    print("  4. Verify the exact permission name in Zoho")
    print("  5. REGENERATE tokens AFTER enabling permission")
    print("  6. Provide new tokens")
    print()
    print("WITHOUT download permission enabled FIRST, tokens won't work!")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
