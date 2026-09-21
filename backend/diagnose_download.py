#!/usr/bin/env python
"""
Inspect the attachment metadata to find how to download the actual file.
The token might be fine, but we might be calling the WRONG endpoint.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

import httpx
import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.models.candidate import Candidate
from app.models.integration_settings import IntegrationSettings

def inspect_and_test():
    """Get metadata and test all possible download patterns."""
    
    print("=" * 70)
    print("INSPECTING METADATA & TESTING DOWNLOAD ENDPOINTS")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get credentials
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            access_token = decrypt_value(integration.access_token_encrypted)
            
            # Get first candidate
            candidate = session.scalar(select(Candidate).limit(1))
            
            if not candidate or not candidate.zoho_candidate_id:
                print("[ERROR] No candidates found")
                return False
            
            print(f"Testing with: {candidate.full_name}")
            print()
            
            base_url = "https://recruit.zoho.in/recruit/v2"
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            with httpx.Client(timeout=30) as client:
                # Get attachments
                response = client.get(
                    base_url + f"/Candidates/{candidate.zoho_candidate_id}/Attachments",
                    headers=headers
                )
                
                attachments = response.json().get('data', [])
                
                if not attachments:
                    print("[ERROR] No attachments")
                    return False
                
                attachment = attachments[0]
                attachment_id = attachment.get('id')
                file_name = attachment.get('File_Name')
                file_id = attachment.get('$file_id')  # This might be the key!
                
                print(f"Attachment: {file_name}")
                print(f"Attachment ID: {attachment_id}")
                print(f"File ID ($file_id): {file_id}")
                print()
                
                # Test 1: Direct file_id endpoint
                print("Test 1: Using $file_id in endpoint...")
                if file_id:
                    response = client.get(
                        f"https://recruit.zoho.in/recruit/api/attachment/download/{file_id}",
                        headers=headers,
                        follow_redirects=True
                    )
                    
                    first_bytes = response.content[:10] if response.content else b''
                    is_binary = first_bytes.startswith(b'%PDF') or first_bytes.startswith(b'PK')
                    
                    print(f"  Endpoint: /recruit/api/attachment/download/{file_id}")
                    print(f"  Status: HTTP {response.status_code}")
                    print(f"  Size: {len(response.content)} bytes")
                    print(f"  First bytes: {first_bytes}")
                    print(f"  Is Binary: {is_binary}")
                    
                    if is_binary:
                        print(f"  ✅ SUCCESS with $file_id!")
                        return True
                    
                    print()
                
                # Test 2: v2 API with file_id
                print("Test 2: v2 API with $file_id parameter...")
                if file_id:
                    response = client.get(
                        base_url + f"/Attachments/{file_id}",
                        headers=headers,
                        follow_redirects=True
                    )
                    
                    first_bytes = response.content[:10] if response.content else b''
                    is_binary = first_bytes.startswith(b'%PDF') or first_bytes.startswith(b'PK')
                    
                    print(f"  Endpoint: {base_url}/Attachments/{file_id}")
                    print(f"  Status: HTTP {response.status_code}")
                    print(f"  Size: {len(response.content)} bytes")
                    print(f"  First bytes: {first_bytes}")
                    print(f"  Is Binary: {is_binary}")
                    
                    if is_binary:
                        print(f"  ✅ SUCCESS with v2 + $file_id!")
                        return True
                    
                    print()
                
                # Test 3: Check if metadata has download URL
                print("Test 3: Looking for download URL in metadata...")
                print(f"  Full metadata keys: {list(attachment.keys())}")
                
                url_candidates = [k for k in attachment.keys() if 'url' in k.lower() or 'download' in k.lower()]
                if url_candidates:
                    print(f"  Found URL-like fields: {url_candidates}")
                    for key in url_candidates:
                        print(f"    {key}: {attachment[key]}")
                else:
                    print(f"  No obvious download URLs in metadata")
                
                print()
                
                # Test 4: Try with different base URLs
                print("Test 4: Trying different base URL patterns...")
                
                patterns = [
                    ("API v2 with ID", f"https://recruit.zoho.in/recruit/v2/Attachments/{attachment_id}/download"),
                    ("API v2.1", f"https://recruit.zoho.in/recruit/v2.1/Attachments/{attachment_id}"),
                    ("Direct API", f"https://recruit.zoho.in/recruit/api/v2/Attachments/{attachment_id}"),
                ]
                
                for name, endpoint in patterns:
                    response = client.get(endpoint, headers=headers, follow_redirects=True)
                    first_bytes = response.content[:10] if response.content else b''
                    is_binary = first_bytes.startswith(b'%PDF') or first_bytes.startswith(b'PK')
                    
                    print(f"  {name}: HTTP {response.status_code}, Binary: {is_binary}")
                    
                    if is_binary:
                        print(f"  ✅ SUCCESS: {endpoint}")
                        return True
                
                print()
                print("=" * 70)
                print("None of the endpoints returned binary file content")
                print("Checking if metadata response contains the file...")
                print("=" * 70)
                
                # Test 5: Maybe the file IS in the metadata response!
                print()
                print("Test 5: Maybe file content is in metadata response...")
                print()
                
                response = client.get(
                    base_url + f"/Attachments/{attachment_id}",
                    headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
                )
                
                metadata = response.json()
                print(f"Response structure:")
                print(json.dumps(metadata, indent=2)[:2000])
                
                return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = inspect_and_test()
    sys.exit(0 if success else 1)
