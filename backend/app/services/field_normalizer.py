"""
Field normalizer for organizing Zoho Recruit data into logical business categories.
Converts raw Zoho payload into a structured, organized format matching business requirements.
"""

from typing import Dict, Any


class CandidateFieldNormalizer:
    """
    Normalizes Zoho Recruit candidate data into proper business categories.
    
    Ensures consistent field organization:
    - Personal Information (core identifier fields)
    - Contact & Address
    - Professional Details
    - Education & Qualifications
    - Application & Recruitment
    - Employment Details
    - Interview Process
    - Candidate Lifecycle
    - Salary & Benefits
    - Referral & Sourcing
    - System & Metadata
    """

    # Mapping of field patterns to categories
    FIELD_CATEGORIES = {
        'Personal Information': {
            'patterns': [
                'First_Name', 'Last_Name', 'Email', 'Phone', 'Mobile', 
                'Date_of_Birth', 'Date_Of_Birth', 'Gender', 'Marital_Status',
                'Nationality', 'Pan_Number'
            ],
            'zoho_keys': ['First_Name', 'Last_Name', 'Email', 'Phone', 'Mobile', 'Date_Of_Birth', 'Gender']
        },
        'Contact & Address': {
            'patterns': [
                'Street', 'City', 'State', 'Zip', 'Country', 'Address',
                'Full_Address', 'Postal_Code', 'Province'
            ],
            'zoho_keys': ['Street', 'City', 'State', 'Zip_Code', 'Country', 'Full_Address']
        },
        'Professional Details': {
            'patterns': [
                'Current_Company', 'Designation', 'Job_Title', 'Years_of_Experience',
                'Experience', 'Skills', 'Current_Role', 'Position', 'Designation',
                'Practice', 'Work_Mode_Location', 'Onsite_Remote', 'WorkStream'
            ],
            'zoho_keys': ['Designation', 'Current_Company', 'Years_of_Experience', 'Experience', 'Skills']
        },
        'Education & Qualifications': {
            'patterns': [
                'Education', 'Degree', 'University', 'Major', 'Grade',
                'Year_of_Graduation', 'Qualification', 'Certificate', 'Certifications',
                'Field_of_Study', 'Institute'
            ],
            'zoho_keys': ['Education', 'Degree', 'University', 'Major', 'Grade', 'Year_of_Graduation']
        },
        'Application & Recruitment': {
            'patterns': [
                'Source', 'Origin', 'Applied_Date', 'Pipeline', 'Stage',
                'Department', 'Recruitment', 'Source_Form', 'Created_Date',
                'Applied_Job_ID', 'Position', 'Client', 'Client_Name', 'Function_Department'
            ],
            'zoho_keys': ['Source', 'Source_Form', 'Origin', 'Applied_Date', 'Created_Date', 'Stage', 'Pipeline', 'Department']
        },
        'Employment Details': {
            'patterns': [
                'Notice_Period', 'Salary', 'CTC', 'Expected', 'Visa_Status',
                'Availability', 'Work_Authorization', 'Employee_Type', 'Employee_Details',
                'Emp_ID', 'Date_of_Joining', 'Date_of_Offer'
            ],
            'zoho_keys': ['Notice_Period', 'Current_Salary', 'Expected_Salary', 'CTC', 'Expected_CTC', 'Visa_Status']
        },
        'Interview Process': {
            'patterns': [
                'Interview', 'L1', 'L2', 'L3', 'L4', 'L5',
                'Panelist', 'Hour', 'Mode', 'URL', 'Feedback',
                'Hiring_Decision', 'Hiring_Mode', 'Client_Interview'
            ],
            'zoho_keys': [
                'L1_Interview_Mode', 'L1_Interview_URL', 'L1_Job_Role', 'L1_Hour',
                'L2_Interview_Mode', 'L2_Interview_URL', 'L2_Job_Role', 'L2_Hour',
                'L3_Interview_Mode', 'L3_Job_Role', 'L3_Hour',
                'L4_Interview', 'L4_Interview_URL', 'L4_Job_Role', 'L4_Hour',
                'L5_Interview_URL', 'Panelist_L1', 'Panelist_L2', 'Panelist_L3'
            ]
        },
        'Candidate Lifecycle': {
            'patterns': [
                'Status', 'Candidate_Status', 'Lead', 'Block', 'Lock',
                'Unqualified', 'Reject', 'LEADPORTALSTATUS', 'Is_Blocked',
                'Is_Locked', 'Is_Unqualified', 'Date_of_Submission', 'Profile_Sent_Date',
                'Resume_Sourced_Date', 'Client_Interview_Status', 'Client_Interview_Date'
            ],
            'zoho_keys': [
                'Candidate_Status', 'LEADPORTALSTATUS', 'Is_Blocked__s', 'Is_Locked',
                'Is_Unqualified', 'Date_of_Submission', 'Profile_Sent_Date',
                'Resume_Sourced_Date', 'Date_of_Offer'
            ]
        },
        'Salary & Benefits': {
            'patterns': [
                'Annual_CTC', 'Basic_Pay', 'Gross_Pay', 'House_Rent',
                'Performance_Bonus', 'Joining_Bonus', 'PF_Contribution',
                'Gratuity', 'Life_Insurance', 'GMC', 'GTLI'
            ],
            'zoho_keys': [
                'Annual_CTC_USD', 'Basic_Pay', 'Gross_Pay_A', 'House_Rent_Allowance',
                'Performance_Bonus', 'Joining_Bonus', 'PF_Contribution_Employer',
                'Gratuity', 'Life_Insurance_Monthly', 'GMC', 'GTLI'
            ]
        },
        'Referral & Sourcing': {
            'patterns': [
                'Vendor', 'Name_of', 'Recruiter', 'Referred', 'Referral',
                'Source_Direct'
            ],
            'zoho_keys': [
                'Vendor', 'Vendor_Name', 'Name_of_Source', 'Name_of_Recruiter',
                'Referred_by_Employee__s', 'Referral_Comments',
                'Source_Direct_Job_Portal_Vendor_Emp_Refer'
            ]
        },
        'System & Metadata': {
            'patterns': [
                'id', 'process_flow', 'approval', 'Modified', 'Created',
                'Last_Mailed', 'Last_Activity', 'Approval_Status'
            ],
            'zoho_keys': ['id', '$process_flow', '$approval', 'Modified_Date', 'Modified_By', 'Last_Mailed_Time', 'Last_Activity_Time']
        }
    }

    @staticmethod
    def normalize(raw_payload: Dict[str, Any], candidate_fields: Dict[str, Any] = None) -> Dict[str, Dict[str, Any]]:
        """
        Normalize Zoho Recruit data into organized business categories.
        
        Args:
            raw_payload: Raw Zoho API response data (all fields)
            candidate_fields: Regular candidate model fields (First_Name, Email, etc.)
        
        Returns:
            Dictionary with categories as keys, each containing normalized fields
            
        Example:
            {
                "Personal Information": {
                    "First Name": "John",
                    "Last Name": "Doe",
                    "Email": "john@example.com",
                    "Phone": "123-456-7890",
                    "Mobile": "987-654-3210",
                    "Date of Birth": "1988-12-14",
                    "Gender": "Male"
                },
                "Contact & Address": {...},
                "Professional Details": {...},
                ...
            }
        """
        normalized = {}
        processed_keys = set()
        
        # Combine candidate fields with raw payload
        all_fields = {**(candidate_fields or {}), **raw_payload}
        
        # First pass: Process each category with its defined fields
        for category, config in CandidateFieldNormalizer.FIELD_CATEGORIES.items():
            category_fields = {}
            
            # Check zoho_keys for this category
            for zoho_key in config.get('zoho_keys', []):
                if zoho_key in all_fields:
                    value = all_fields[zoho_key]
                    if CandidateFieldNormalizer._has_value(value):
                        field_name = CandidateFieldNormalizer._format_field_name(zoho_key)
                        # Extract readable value (handles nested objects)
                        readable_value = CandidateFieldNormalizer._extract_readable_value(value)
                        category_fields[field_name] = readable_value
                        processed_keys.add(zoho_key)
            
            if category_fields:
                normalized[category] = category_fields
        
        # Second pass: Add any remaining unprocessed fields to "Other Fields"
        other_fields = {}
        for key, value in all_fields.items():
            if key not in processed_keys and CandidateFieldNormalizer._has_value(value):
                field_name = CandidateFieldNormalizer._format_field_name(key)
                readable_value = CandidateFieldNormalizer._extract_readable_value(value)
                other_fields[field_name] = readable_value
        
        if other_fields:
            normalized['Other Fields'] = other_fields
        
        return normalized

    @staticmethod
    def _extract_readable_value(value: Any) -> str:
        """Extract readable value from any field type, including nested objects."""
        if value is None:
            return '—'
        
        # Handle booleans
        if isinstance(value, bool):
            return 'Yes' if value else 'No'
        
        # Handle objects/dicts - extract 'name' field if available
        if isinstance(value, dict):
            # Try to get 'name' field for Zoho linked records
            if 'name' in value:
                return str(value['name']).strip()
            # Try to get first non-empty value
            for v in value.values():
                if v and isinstance(v, str):
                    return str(v).strip()
            # Fallback: return dict summary
            return f"(object with {len(value)} fields)"
        
        # Handle lists
        if isinstance(value, list):
            if len(value) == 0:
                return '—'
            # Join non-empty list items
            items = [str(v).strip() for v in value if v]
            return ', '.join(items) if items else '—'
        
        # Handle strings
        str_value = str(value).strip()
        return str_value if str_value else '—'

    @staticmethod
    def _has_value(value: Any) -> bool:
        """Check if value is not empty."""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True  # Booleans are always meaningful
        return True  # Other types (numbers, etc.) are always meaningful

    @staticmethod
    def _format_field_name(field_key: str) -> str:
        """Convert Zoho field name to readable display name."""
        # Remove leading $ (for system fields)
        field_key = field_key.lstrip('$')
        
        # Replace underscores with spaces
        field_name = field_key.replace('_', ' ')
        
        # Convert to Title Case
        field_name = field_name.title()
        
        # Fix specific patterns
        field_name = field_name.replace('__s', '')  # Remove Zoho's __s suffix
        field_name = field_name.replace('Ctc', 'CTC')
        field_name = field_name.replace('Pf', 'PF')
        field_name = field_name.replace('Gtli', 'GTLI')
        field_name = field_name.replace('Gmc', 'GMC')
        field_name = field_name.replace('Emp ', 'Emp. ')
        field_name = field_name.replace('Of ', 'of ')
        
        return field_name
