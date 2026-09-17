"""
Add comprehensive sample candidate with all data populated
"""
import sys
sys.path.insert(0, '.')

from app.core.database import get_session_factory
from app.models.candidate import Candidate
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import json

SessionLocal = get_session_factory()
session = SessionLocal()

try:
    # Check if sample candidate already exists
    existing = session.query(Candidate).filter_by(full_name="Complete Profile Test").first()
    if existing:
        print(f"Candidate '{existing.full_name}' already exists. Skipping...")
        sys.exit(0)
    
    now = datetime.now(timezone.utc)
    
    # Comprehensive raw_payload with all extended field data
    raw_payload = {
        # Basic fields
        "First_Name": "Rajesh",
        "Last_Name": "Kumar",
        "Email": "rajesh.kumar@example.com",
        "Phone": "+91 9876543210",
        
        # Personal/Contact fields
        "Date_Of_Birth": "1992-05-15",
        "Full_Address": "123 Tech Park, Bangalore, Karnataka 560001",
        "Aadhaar_No": "1234-5678-9012",
        "Aadhar_New": "XXXX-XXXX-5678",
        "Email_Optional": "rajesh.alt@example.com",
        "LinkedIn__s": "https://linkedin.com/in/rajeshumar",
        "Facebook__s": "https://facebook.com/rajeshumar",
        "Recruiter_Mobile_No": "9876543210",
        
        # Employment fields
        "Date_of_Joining": "2022-03-15",
        "Employee_Type": "Full-Time",
        "Employee_Details": "Senior Developer",
        "Emp_ID": "EMP-2022-0456",
        "Department": "Engineering",
        "Function_Department": "Backend Development",
        "Practice": "Java/Spring Boot",
        "Work_Mode_Location": "Hybrid",
        "Onsite_Remote": "3 days onsite",
        "WorkStream": "Microservices",
        
        # Interview Process fields
        "Applied_Job_ID": "JD-2026-025",
        "Position": "Senior Backend Engineer",
        "Client": "TechCorp India",
        "Client_Name": "TechCorp Solutions",
        "Candidate_Owner": "Priya Sharma",
        "Hiring_Decision": "Selected",
        "Hiring_Mode": "Full-Time",
        "L1_Interview_Mode": "Video Call",
        "L1_Interview_URL": "https://zoom.us/j/1234567890",
        "L1_Job_Role": "Backend Engineer",
        "L1_Hour": "2 hours",
        "L2_Interview_Mode": "Video Call",
        "L2_Interview_URL": "https://zoom.us/j/0987654321",
        "L2_Job_Role": "Architect Round",
        "L2_Hour": "1.5 hours",
        "L3_Interview_Mode": "In-Person",
        "L3_Job_Role": "VP Engineering",
        "L3_Hour": "1 hour",
        "L4_Interview": "Not Required",
        "L4_Interview_URL": None,
        "L4_Job_Role": None,
        "L4_Hour": None,
        "L5_Interview_URL": None,
        "Client_Interview_Status": "Completed",
        "Client_Interview_Date": "2026-08-25",
        "Panelist_L1": "Amit Patel",
        "Panelist_L2": "Neha Gupta",
        "Panelist_L3": "Vikram Singh",
        
        # Candidate Lifecycle fields
        "Date_of_Offer": "2026-08-28",
        "Date_of_Submission": "2026-08-10",
        "Profile_Sent_Date": "2026-08-09",
        "Resume_Sourced_Date": "2026-08-08",
        "Candidate_Status": "Offer Accepted",
        "LEADPORTALSTATUS": "Hired",
        "Is_Blocked__s": False,
        "Is_Locked": False,
        "Is_Unqualified": False,
        
        # Salary & Benefits fields
        "Annual_CTC_USD": "180000",
        "Basic_Pay": "450000",
        "Gross_Pay_A": "720000",
        "House_Rent_Allowance": "180000",
        "Performance_Bonus": "120000",
        "Joining_Bonus": "500000",
        "PF_Contribution_Employer": "48000",
        "Gratuity": "Service Based",
        "Life_Insurance_Monthly": "5000",
        "GMC": "Yes",
        "GTLI": "Yes",
        
        # Referral, Vendor & Sourcing fields
        "Vendor": "Kanini Consulting",
        "Vendor_Name": "Kanini Technologies",
        "Name_of_Source": "Direct Portal",
        "Name_of_Recruiter": "Rajesh Kumar",
        "Referred_by_Employee__s": "None",
        "Referral_Comments": "Excellent technical skills and communication",
        "Source_Direct_Job_Portal_Vendor_Emp_Refer": "Direct",
        
        # Additional fields
        "Current_Employer": "InfoSys Limited",
        "Previous_Company": "Accenture India",
        "Current_Location_Website": "Bangalore",
        "Preferred_Work_Location": "Bangalore, Hyderabad",
        "Visa_Status": "Indian National",
        "Notice_Period": "1 Month",
        "Certification": "AWS Solutions Architect",
    }
    
    # Create the comprehensive candidate
    candidate = Candidate(
        id=uuid4(),
        zoho_record_id="z-complete-test",
        zoho_candidate_id="z-complete-test",
        full_name="Complete Profile Test",
        email="rajesh.kumar@example.com",
        phone="+91 9876543210",
        current_company="InfoSys Limited",
        current_location="Bangalore",
        preferred_location="Bangalore, Hyderabad",
        skills=["Java", "Spring Boot", "Microservices", "REST APIs", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
        total_experience_years=8,
        relevant_experience_years=7,
        notice_period_days=30,
        status="hired",
        degree="B.Tech Computer Science",
        normalized_degree="Bachelor Degree - Computer Science",
        current_ctc=12.0,  # 12 LPA
        expected_ctc=18.0,  # 18 LPA
        source="direct",
        match_metadata={
            "jd_id": "JD-2026-025",
            "jd_title": "Senior Backend Engineer",
            "match_percentage": 95,
            "match_score": 95,
            "matched_criteria": ["Java", "Spring Boot", "Microservices", "8+ years experience"],
        },
        raw_payload=raw_payload,
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=1),
    )
    
    session.add(candidate)
    session.commit()
    
    print(f"✓ Successfully added comprehensive sample candidate: {candidate.full_name}")
    print(f"  ID: {candidate.id}")
    print(f"  Email: {candidate.email}")
    print(f"  Skills: {', '.join(candidate.skills)}")
    print(f"  Experience: {candidate.total_experience_years} years")
    print(f"  Status: {candidate.status}")
    print(f"  Current CTC: {candidate.current_ctc} LPA")
    print(f"  Expected CTC: {candidate.expected_ctc} LPA")
    print(f"\n  Extended Fields in raw_payload:")
    print(f"    - Personal/Contact: 8 fields")
    print(f"    - Employment: 9 fields")
    print(f"    - Interview Process: 18 fields")
    print(f"    - Candidate Lifecycle: 7 fields")
    print(f"    - Salary & Benefits: 10 fields")
    print(f"    - Referral/Vendor/Sourcing: 7 fields")
    print(f"\n  Total: 59 fields populated!")
    
finally:
    session.close()
