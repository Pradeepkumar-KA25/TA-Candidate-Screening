from app.services.multi_line_experience_parser import parse_experience_multiline, validate_and_enhance_experience

# Test with exact resume format
lines = [
    'UST                                          Pune, India',
    'Lead Data & GenAI Engineer                   October 2023 - Present',
    '• Architected end-to-end cloud-native data pipelines',
    '• Designed scalable BigQuery warehouse models',
]

print('Testing parsing with:')
for line in lines:
    print(f'  {repr(line)}')

experiences = parse_experience_multiline(lines)
print(f'\nParsed {len(experiences)} experience(s)')

for i, exp in enumerate(experiences, 1):
    print(f'\nExperience {i}:')
    print(f'  Company: {repr(exp.get("company"))}')
    print(f'  Title: {repr(exp.get("title"))}')
    print(f'  Location: {repr(exp.get("location"))}')
    print(f'  Dates: {repr(exp.get("dates"))}')
    print(f'  Responsibilities: {len(exp.get("responsibilities", []))} items')

# Now validate/enhance
print('\n--- After Enhancement ---')
enhanced = validate_and_enhance_experience(experiences)
for i, exp in enumerate(enhanced, 1):
    print(f'\nExperience {i}:')
    print(f'  Company: {repr(exp.get("company"))}')
    print(f'  Title: {repr(exp.get("title"))}')
    print(f'  Location: {repr(exp.get("location"))}')
    print(f'  Dates: {repr(exp.get("dates"))}')
