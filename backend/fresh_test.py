#!/usr/bin/env python3
"""Fresh test without module caching."""
import sys
import importlib

# Force reload
if 'app.services.experience_extraction_enhancer' in sys.modules:
    del sys.modules['app.services.experience_extraction_enhancer']

sys.path.insert(0, '.')
from app.services.experience_extraction_enhancer import validate_and_correct_experience

exp = {
    "company": "Pune, India",
    "title": "UST",
    "location": "",
    "dates": "October 2023 – Present",
    "responsibilities": ["Test"],
}

print(f"Before:")
print(f"  company: {exp['company']}")
print(f"  title: {exp['title']}")
print(f"  location: {exp['location']}")

result = validate_and_correct_experience(exp)

print(f"\nAfter:")
print(f"  company: {result['company']}")
print(f"  title: {result['title']}")
print(f"  location: {result['location']}")

if result['company'] == "UST" and result['location'] == "Pune, India":
    print("\n✓ PASS")
else:
    print(f"\n✗ FAIL - Expected company='UST', location='Pune, India'")
    print(f"  Got company='{result['company']}', location='{result['location']}'")
