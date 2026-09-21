#!/usr/bin/env python
"""Diagnose Zoho attachment endpoints to find correct download method."""

import os
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import json

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.models.integration_settings import IntegrationSettings
import httpx

def diagnose_attachments():
    """Diagnose Zoho attachment endpoints."""
    
    print("="*70)
    print("ZOHO ATTACHMENT ENDPOINT DIAGNOSIS")
    print("="*70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get Zoho integration
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[FAIL] No Zoho integration found")
                return False
            
            access_token = decrypt_value(integration.access_token_encrypted)
            base_url = settings.zoho_recruit_base_url.rstrip("/")
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            print("[OK] Connected to Zoho")
            print("Base URL: " + base_url)
            print()
            
            # Get a candidate with attachments
            zoho_client = ZohoRecruitClient()
            candidates = list(zoho_client.iter_candidates(access_token, per_page=10))
            
            if not candidates:
                print("[FAIL] No candidates found")
                return False
            
            # Find candidate with attachments
            test_candidate = None
            test_attachment = None
            
            for candidate in candidates:
                candidate_id = candidate.get("id")
                candidate_name = candidate.get("Full_Name", "Unknown")
                
                try:
                    attachments = zoho_client.fetch_candidate_attachments(access_token, candidate_id)
                    if attachments:
                        test_candidate = {"id": candidate_id, "name": candidate_name}
                        test_attachment = attachments[0]
                        break
                except:
                    continue
            
            if not test_attachment:
                print("[FAIL] No candidates with attachments found")
                return False
            
            attachment_id = test_attachment.get("id")
            file_name = test_attachment.get("File_Name", "unknown")
            
            print("[OK] Test Candidate: " + test_candidate['name'])
            print("[OK] Test Attachment: " + file_name)
            print("[OK] Attachment ID: " + attachment_id)
            print()
            print("="*70)
            print("TESTING DIFFERENT HEADER COMBINATIONS")
            print("="*70)
            print()
            
            # Test different header combinations
            test_cases = [
                ("No Accept header", {}),
                ("Accept: application/octet-stream", {"Accept": "application/octet-stream"}),
                ("Accept: */*", {"Accept": "*/*"}),
                ("Accept: application/pdf", {"Accept": "application/pdf"}),
                ("Accept: application/json", {"Accept": "application/json"}),
            ]
            
            best_response = None
            best_case_name = None
            
            with httpx.Client(timeout=30) as client:
                for case_name, extra_headers in test_cases:
                    print("Testing: " + case_name)
                    request_headers = {**headers, **extra_headers}
                    endpoint = base_url + "/Attachments/" + attachment_id
                    
                    try:
                        response = client.get(endpoint, headers=request_headers)
                        
                        print("  Status: " + str(response.status_code))
                        print("  Content-Type: " + response.headers.get('content-type', 'not set'))
                        print("  Size: " + str(len(response.content)) + " bytes")
                        
                        # Analyze response
                        first_bytes = response.content[:20] if response.content else b''
                        
                        if first_bytes.startswith(b'%PDF'):
                            print("  [BINARY] PDF file detected!")
                            best_response = response
                            best_case_name = case_name
                        elif first_bytes.startswith(b'PK'):
                            print("  [BINARY] DOCX/ZIP file detected!")
                            best_response = response
                            best_case_name = case_name
                        elif first_bytes[:2] in [b'\xd0\xcf', b'\xfd\xff']:
                            print("  [BINARY] DOC file detected!")
                            best_response = response
                            best_case_name = case_name
                        elif first_bytes.startswith(b'{') or first_bytes.startswith(b'['):
                            print("  [JSON] Metadata response")
                            # Show JSON keys
                            try:
                                data = json.loads(response.content)
                                if isinstance(data, dict) and 'data' in data:
                                    keys = list(data['data'][0].keys()) if data['data'] else []
                                    print("  Keys: " + str(keys[:5]))
                            except:
                                pass
                        else:
                            print("  [UNKNOWN] " + first_bytes.hex()[:20])
                        
                        print()
                        
                        # Stop if we found binary
                        if best_response:
                            break
                        
                    except Exception as e:
                        print("  [ERROR] " + str(e))
                        print()
                        continue
            
            print("="*70)
            if best_response:
                print("[SUCCESS]")
                print("Working header: " + best_case_name)
                print("File size: " + str(len(best_response.content)) + " bytes")
                print("Can be used in download_attachment()")
                return True
            else:
                print("[FAILED] No working endpoint found")
                print()
                print("Possible solutions:")
                print("1. Check if Zoho API requires different authentication")
                print("2. Some attachments might not be downloadable")
                print("3. Zoho might require additional setup/permissions")
                return False
        
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = diagnose_attachments()
    exit(0 if success else 1)
