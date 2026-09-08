"""Service for generating Excel exports of shortlists."""

from datetime import datetime
from io import BytesIO
from uuid import UUID

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.shortlist import Shortlist
from app.models.shortlist_candidate import ShortlistCandidate


class ExcelExportService:
    """Service for generating Excel exports of shortlists."""

    def __init__(self, session: Session):
        """Initialize the ExcelExportService with a database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def generate_shortlist_export(self, shortlist_id: UUID) -> tuple[bytes, str]:
        """Generate a formatted Excel workbook for a shortlist.
        
        Args:
            shortlist_id: UUID of the shortlist to export
            
        Returns:
            Tuple of (Excel file bytes, suggested filename)
            
        Raises:
            ValueError: If shortlist not found or has no candidates
        """
        # Fetch shortlist with related data
        shortlist = self.session.query(Shortlist).filter(Shortlist.id == shortlist_id).first()
        if not shortlist:
            raise ValueError(f"Shortlist {shortlist_id} not found")

        # Fetch JD for naming and info
        jd = self.session.query(JobDescription).filter(JobDescription.id == shortlist.jd_id).first()
        if not jd:
            raise ValueError(f"JobDescription {shortlist.jd_id} not found")

        # Fetch candidate IDs from shortlist
        shortlist_candidates = (
            self.session.query(ShortlistCandidate)
            .filter(ShortlistCandidate.shortlist_id == shortlist_id)
            .all()
        )
        
        if not shortlist_candidates:
            raise ValueError("Shortlist has no candidates")

        candidate_ids = [sc.candidate_id for sc in shortlist_candidates]

        # Fetch candidate data in the order they appear in shortlist
        candidates = self.session.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
        
        # Create workbook and add data
        wb = Workbook()
        ws = wb.active
        ws.title = "Shortlist"

        # Add headers
        headers = [
            "Record Id", "Candidate Owner", "Staffing Clients", "First Name", "Last Name",
            "Email", "Skill Set", "Practice", "Source", "Employee Details", "State/Province",
            "Job ID", "Phone", "City", "Country", "Date of Submission", "Job Title as per KANINI",
            "Date of Joining", "Name of Source", "Current Work Location", "Experience in Yrs",
            "Total Years of Exp", "Job Role", "Practice", "Stream", "Department",
            "Job Role as per Kanini", "Overall IT Experince", "Role Relevant Exp", "LinkedIn",
        ]
        ws.append(headers)

        # Format header row
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Add candidate data
        for candidate in candidates:
            raw_payload = candidate.raw_payload if isinstance(candidate.raw_payload, dict) else {}
            full_name_parts = (candidate.full_name or "").split(maxsplit=1)
            first_name = self._payload_value(raw_payload, "First_Name") or (full_name_parts[0] if full_name_parts else "")
            last_name = self._payload_value(raw_payload, "Last_Name") or (full_name_parts[1] if len(full_name_parts) > 1 else "")
            skills = self._payload_value(raw_payload, "Skill_Set", "Skills") or ", ".join(candidate.skills or [])
            row = [
                candidate.zoho_record_id or candidate.zoho_candidate_id or "",
                self._payload_value(raw_payload, "Candidate_Owner"),
                self._payload_value(raw_payload, "Staffing_Clients"),
                first_name,
                last_name,
                candidate.email or "",
                skills,
                self._payload_value(raw_payload, "Practice"),
                candidate.source or self._payload_value(raw_payload, "Source"),
                self._payload_value(raw_payload, "Employee_Details", "Employer_Details") or candidate.current_company or "",
                self._payload_value(raw_payload, "State", "State_Province"),
                self._payload_value(raw_payload, "Job_ID", "Job_Id"),
                candidate.phone or self._payload_value(raw_payload, "Phone"),
                self._payload_value(raw_payload, "City"),
                self._payload_value(raw_payload, "Country"),
                self._payload_value(raw_payload, "Date_of_Submission"),
                self._payload_value(raw_payload, "Job_Title_as_per_KANINI"),
                self._payload_value(raw_payload, "Date_of_Joining"),
                self._payload_value(raw_payload, "Name_of_Source") or candidate.source or "",
                self._payload_value(raw_payload, "Current_Work_Location", "Current_Location") or candidate.current_location or "",
                self._payload_value(raw_payload, "Experience_in_Yrs", "Experience_in_Years") or candidate.total_experience_years or "",
                self._payload_value(raw_payload, "Total_Years_of_Exp") or candidate.total_experience_years or "",
                self._payload_value(raw_payload, "Job_Role"),
                self._payload_value(raw_payload, "Practice"),
                self._payload_value(raw_payload, "Stream"),
                self._payload_value(raw_payload, "Department"),
                self._payload_value(raw_payload, "Job_Role_as_per_Kanini"),
                self._payload_value(raw_payload, "Overall_IT_Experince") or candidate.total_experience_years or "",
                self._payload_value(raw_payload, "Role_Relevant_Exp", "Relevant_Experience", "Relevant_Exp") or candidate.relevant_experience_years or "",
                self._payload_value(raw_payload, "LinkedIn", "LinkedIn_URL"),
            ]
            ws.append(row)

        # Add summary section
        ws.append([])  # Blank row
        ws.append(["Export Summary"])
        ws.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        ws.append([f"Job Description: {jd.title}"])
        ws.append([f"JD Code: {jd.jd_code}"])
        ws.append([f"Candidate Count: {len(candidates)}"])

        # Adjust column widths
        for column_index, header in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(column_index)].width = min(max(len(header) + 4, 16), 32)

        # Generate filename
        filename = self._generate_filename(jd.title)

        # Write to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        file_bytes = output.getvalue()

        return file_bytes, filename

    @staticmethod
    def _payload_value(raw_payload: dict, *keys: str) -> str | int | float:
        """Return the first displayable Zoho payload value for the supplied keys."""
        for key in keys:
            value = raw_payload.get(key)
            if isinstance(value, dict):
                value = value.get("name") or value.get("Name") or value.get("value")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value if item is not None)
            if isinstance(value, (str, int, float)):
                value = value.strip() if isinstance(value, str) else value
                if value != "":
                    return value
        return ""

    @staticmethod
    def _generate_filename(jd_title: str) -> str:
        """Generate a descriptive filename from JD title.
        
        Args:
            jd_title: Title of the job description
            
        Returns:
            Formatted filename (e.g., 'Java_Backend_Shortlist.xlsx')
        """
        # Replace spaces with underscores, remove special characters
        sanitized = jd_title.replace(" ", "_").replace("/", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        return f"{sanitized}_Shortlist.xlsx"
