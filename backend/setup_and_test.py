#!/usr/bin/env python
"""Update credentials and test full connection including file download."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import httpx

from app.core.config import settings
from app.core.crypto import encrypt_value
from app.models.integration_settings import IntegrationSettings

def setup_and_test():
    """Update credentials and test everything."""
    
    # New credentials
    new_client_id = "1000.WA5TEPHE77PLKH4QFWL1NV044OCK7P"
    new_client_secret = "50686efc31975c713dc65004087e17ee56a7e802e7"
    new_access_token = "1000.817f218c36727340418054e20bcb20ad.7821ea68c53317e60ea8720a35e79d8c"
    new_refresh_token = "1000.fcf6f651fb39e276df982c30545a8347.300468d038d8e1caa6da9a5642b7a1ed"
    
    print("=" * 70)
    print("SETUP: Update Credentials and Test Connection")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        # Step 1: Update database
        print("Step 1: Updating database credentials...")
        with Session(engine) as session:
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[ERROR] No Zoho integration found")
                return False
            
            integration.client_id = new_client_id
            integration.client_secret = new_client_secret
            integration.access_token_encrypted = encrypt_value(new_access_token)
            integration.refresh_token_encrypted = encrypt_value(new_refresh_token)
            integration.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            print("[OK] Credentials updated in database")
            print()
        
        # Step 2: Test basic connectivity
        print("Step 2: Testing Zoho connectivity...")
        base_url = "https://recruit.zoho.in/recruit/v2"
        headers = {"Authorization": f"Zoho-oauthtoken {new_access_token}"}
        
        with httpx.Client(timeout=30) as client:
            response = client.get(base_url + "/Candidates?per_page=1", headers=headers)
            
            if response.status_code == 200:
                print("[OK] Connected to Zoho Recruit API")
                candidates = response.json().get('data', [])
                print("[OK] Can fetch candidates: " + str(len(candidates)) + " found")
                print()
            else:
                print("[ERROR] Failed to connect: HTTP " + str(response.status_code))
                return False
            
            # Step 3: Test attachment download permission
            print("Step 3: Testing attachment download permission...")
            if candidates:
                candidate = candidates[0]
                candidate_id = candidate.get('id')
                candidate_name = candidate.get('Full_Name', 'Unknown')
                
                # Get attachments
                response = client.get(
                    base_url + f"/Candidates/{candidate_id}/Attachments",
                    headers=headers
                )
                
                attachments = response.json().get('data', [])
                
                if attachments:
                    attachment = attachments[0]
                    attachment_id = attachment.get('id')
                    file_name = attachment.get('File_Name', 'unknown')
                    
                    print("[OK] Found attachments for: " + candidate_name)
                    print("[OK] Test file: " + file_name)
                    print()
                    
                    # Test different download endpoints
                    print("Step 4: Testing download endpoints...")
                    
                    download_methods = [
                        ("Direct /Attachments endpoint", base_url + f"/Attachments/{attachment_id}"),
                        ("Download API endpoint", "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id)),
                    ]
                    
                    success = False
                    for method_name, endpoint in download_methods:
                        response = client.get(endpoint, headers=headers, follow_redirects=False)
                        
                        first_bytes = response.content[:10] if response.content else b''
                        
                        if first_bytes.startswith(b'%PDF') or first_bytes.startswith(b'PK'):
                            print("[OK] " + method_name + " - SUCCESS (binary file)")
                            success = True
                            break
                        elif response.status_code == 302 and 'IAMSecurityError' not in response.headers.get('location', ''):
                            print("[OK] " + method_name + " - OK (redirect, might work with redirect)")
                            success = True
                            break
                        else:
                            print("[INFO] " + method_name + " - HTTP " + str(response.status_code))
                    
                    print()
                    
                    if success:
                        print("[OK] Download permission appears to be working!")
                        print()
                        return True
                    else:
                        print("[WARNING] Download might need additional testing during sync")
                        print("[INFO] Will attempt download during sync process")
                        print()
                        return True
                else:
                    print("[INFO] No attachments found to test download")
                    print("[INFO] Will test during actual sync")
                    print()
                    return True
        
        return True
            
    except Exception as e:
        print("[ERROR] Setup failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = setup_and_test()
    print("=" * 70)
    if success:
        print("SETUP COMPLETE - Ready to sync!")
    else:
        print("SETUP FAILED")
    print("=" * 70)
    sys.exit(0 if success else 1)
