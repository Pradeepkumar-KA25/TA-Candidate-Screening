#!/usr/bin/env python
"""Test if Zoho tokens are valid by fetching candidates."""

import httpx

def test_tokens():
    """Test Zoho tokens directly."""
    
    # Tokens provided
    access_token = "1000.0287eee2d7787850a27791b6b811bc20.f23fba24c17c53aee04e3ac7ee4f958a"
    refresh_token = "1000.016538f89cf868d52ec10a5b687e5754.938160967bfaf48393a18f82bb3c659c"
    client_id = "1000.WA5TEPHE77PLKH4QFWL1NV044OCK7P"
    client_secret = "50686efc31975c713dc65004087e17ee56a7e802e7"
    
    print("=" * 70)
    print("ZOHO TOKEN VALIDATION TEST")
    print("=" * 70)
    print()
    
    base_url = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    print("Step 1: Testing Access Token")
    print("-" * 70)
    print("Access Token: " + access_token[:40] + "...")
    print()
    
    try:
        with httpx.Client(timeout=30) as client:
            print("Attempting to fetch candidates from Zoho...")
            response = client.get(
                base_url + "/Candidates?per_page=5",
                headers=headers
            )
            
            print("HTTP Status Code: " + str(response.status_code))
            print("Content-Type: " + response.headers.get('content-type', 'unknown'))
            print()
            
            if response.status_code == 200:
                print("[SUCCESS] Token is VALID!")
                print()
                
                data = response.json()
                candidates = data.get('data', [])
                
                print("Candidates Retrieved: " + str(len(candidates)))
                print()
                
                if candidates:
                    print("Sample Candidate Data:")
                    print("-" * 70)
                    for i, candidate in enumerate(candidates[:3], 1):
                        print("Candidate " + str(i) + ":")
                        print("  Name: " + candidate.get('Full_Name', 'N/A'))
                        print("  Email: " + candidate.get('Email', 'N/A'))
                        print("  ID: " + str(candidate.get('id', 'N/A')))
                        print()
                    
                    return True
                else:
                    print("[INFO] No candidates found in this Zoho account")
                    return True
                    
            elif response.status_code == 401:
                print("[ERROR] INVALID TOKEN")
                print()
                try:
                    error = response.json()
                    print("Error Code: " + error.get('code', 'unknown'))
                    print("Error Message: " + error.get('message', 'unknown'))
                except:
                    print("Response: " + response.text)
                return False
                
            elif response.status_code == 403:
                print("[ERROR] ACCESS FORBIDDEN")
                print("Token is valid but lacks permission to fetch candidates")
                print("Response: " + response.text[:200])
                return False
                
            else:
                print("[ERROR] HTTP " + str(response.status_code))
                print("Response: " + response.text[:300])
                return False
                
    except Exception as e:
        print("[ERROR] Connection failed: " + str(e))
        return False

if __name__ == "__main__":
    success = test_tokens()
    exit(0 if success else 1)
