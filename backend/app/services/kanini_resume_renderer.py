"""
Kanini Resume Renderer - Generate HTML/PDF/DOCX from parsed resume data
Exactly matches Kanini project's template formats (Format 1 & 2)
"""

import html as html_escape
import re
from typing import Dict, Any
from pathlib import Path


class KaniniResumeRenderer:
    """Renders resume data to HTML, PDF, or DOCX formats using Kanini design system."""

    # Template 1 CSS (Format 1 - Letter size)
    TEMPLATE1_CSS = """@page { size: letter; margin: 1in 0 0; }
html, body { margin: 0; padding: 0; background: #fff; }
.kanini-logo { width: 50px; height: auto; margin: -10px 0 10px -10px; display: block; }
.resume-page { box-sizing: border-box; width: 8.5in; min-height: 11in; margin: 0 auto; padding: 1in; color: #000; font: 12pt/1.2 "Times New Roman", serif; background: #fff; }
.resume-name { margin: 0 0 6pt; color: #000000; text-align: center; font: 700 12pt "Times New Roman", serif; text-transform: uppercase; }
.resume-contact { margin: 0 0 12pt; text-align: center; font-size: 11pt; }
.resume-section { margin-top: 14pt; break-inside: avoid; }
.resume-section > h2, .project-title, .responsibilities-title { margin: 0 0 4pt; color: #000000; font: 700 12pt "Times New Roman", serif; text-transform: uppercase; }
.resume-section p { margin: 0 0 4pt; text-align: justify; }
.resume-section ul { margin: 3pt 0 0 18pt; padding-left: 18pt; }
.resume-section li { margin-bottom: 3pt; }
.experience { margin: 5pt 0 10pt; break-inside: avoid; }
.label-row { display: grid; grid-template-columns: 120pt 14pt minmax(0, 1fr); margin: 0 0 0 36pt; }
.project { margin: 9pt 0 12pt; break-inside: avoid; }
@media screen { .resume-page { box-shadow: 0 1px 5px rgb(0 0 0 / 22%); } }"""

    # Template 2 CSS (Format 2 - A4 size, Deloitte style)
    TEMPLATE2_CSS = """@page { size: A4; margin: 1in 0 0; }
html, body { margin: 0; padding: 0; background: #fff; }
.kanini-logo { width: 65px; height: auto; margin: -10px 0 10px -10px; display: block; }
.resume-page { width: 210mm; min-height: 297mm; box-sizing: border-box; padding: 1in 12pt 18pt 46pt; margin: 0 auto; background: #fff; color: #000; font: 12pt/1.15 "Times New Roman", serif; }
h1, h2, h3, h4 { color: #000000; font-size: 12pt; margin: 8pt 0 3pt; font-weight: 700; text-transform: uppercase; }
h1 { text-align: center; margin: 0 0 14pt; }
p { margin: 0 0 2pt; }
.row { display: grid; grid-template-columns: 190pt 14pt minmax(0, 1fr); margin-left: 10pt; }
article { break-inside: avoid; }
ul { margin: 2pt 0 4pt 39pt; padding-left: 18pt; }
@media screen { .resume-page { box-shadow: 0 1px 5px #999; } }"""

    @staticmethod
    def render_html(resume_data: Dict[str, Any], template_id: str = "template1") -> str:
        """Render resume as HTML matching Kanini design."""
        contact = resume_data.get("contact", {})
        summary = resume_data.get("summary", "")
        skills = resume_data.get("skills", {})
        experience = resume_data.get("experience", [])
        education = resume_data.get("education", [])
        projects = resume_data.get("projects", [])
        certifications = resume_data.get("certifications", [])
        achievements = resume_data.get("achievements", [])

        # Build contact info - ONLY NAME, NO PERSONAL DETAILS
        # Skip phone, email, location, linkedin, github from preview
        contact_html = ""

        # Select CSS based on template
        css = KaniniResumeRenderer.TEMPLATE1_CSS if template_id == "template1" else KaniniResumeRenderer.TEMPLATE2_CSS

        # Build sections
        sections = []

        # Profile Summary
        if summary:
            summary_lines = [line.strip() for line in summary.strip().split('\n') if line.strip()]
            summary_html = f"""<section class="resume-section">
<h2>Profile Summary</h2>
<ul>
{''.join(f'<li>{html_escape.escape(line)}</li>' + chr(10) for line in summary_lines)}
</ul>
</section>"""
            sections.append(summary_html)

        # Technical Skills
        if skills:
            skills_html = """<section class="resume-section">
<h2>Technical Skills</h2>
<ul>
"""
            if isinstance(skills, dict):
                for category, skill_list in skills.items():
                    if isinstance(skill_list, (list, tuple)):
                        skills_items = ", ".join(str(s) for s in skill_list)
                    else:
                        skills_items = str(skill_list)
                    skills_html += f"<li><strong>{html_escape.escape(str(category))}:</strong> {html_escape.escape(skills_items)}</li>\n"
            elif isinstance(skills, str):
                skill_lines = [line.strip() for line in skills.strip().split('\n') if line.strip()]
                for line in skill_lines:
                    skills_html += f"<li>{html_escape.escape(line)}</li>\n"

            skills_html += """</ul>
</section>"""
            sections.append(skills_html)

        # Work Experience
        if experience:
            exp_html = """<section class="resume-section">
<h2>Work Experience</h2>
"""
            for exp in experience:
                title = exp.get('title', '') or exp.get('job_title', '')
                company = exp.get('company', '') or exp.get('company_name', '')
                dates = exp.get('dates', '')
                responsibilities = exp.get('responsibilities', [])

                css_class = "row" if template_id == "template2" else "label-row"
                exp_html += f"""<div class="experience">
<div class="{css_class}">
<span>Company Name</span>
<span>:</span>
<span>{html_escape.escape(str(company or '-'))}</span>
</div>
<div class="{css_class}">
<span>Designation</span>
<span>:</span>
<span>{html_escape.escape(str(title or '-'))}</span>
</div>
<div class="{css_class}">
<span>Duration</span>
<span>:</span>
<span>{html_escape.escape(str(dates or '-'))}</span>
</div>
"""
                if responsibilities:
                    exp_html += "<ul>\n"
                    for resp in responsibilities:
                        exp_html += f"<li>{html_escape.escape(str(resp))}</li>\n"
                    exp_html += "</ul>\n"

                exp_html += "</div>\n"

            exp_html += "</section>"
            sections.append(exp_html)

        # Projects
        if projects:
            proj_html = """<section class="resume-section">
<h2>Project Summary</h2>
"""
            if isinstance(projects, str):
                # Handle projects as a single string with line breaks
                proj_list = [line.strip() for line in projects.strip().split('\n') if line.strip()]
                for idx, proj_text in enumerate(proj_list, 1):
                    roman_idx = KaniniResumeRenderer._to_roman(idx)
                    proj_html += f"""<article class="project">
<div class="project-title">Project {roman_idx}:</div>
<p>{html_escape.escape(proj_text)}</p>
</article>
"""
            else:
                # Handle projects as a list
                for idx, proj in enumerate(projects, 1):
                    if isinstance(proj, str):
                        # Project is a string
                        roman_idx = KaniniResumeRenderer._to_roman(idx)
                        proj_html += f"""<article class="project">
<div class="project-title">Project {roman_idx}:</div>
<p>{html_escape.escape(proj)}</p>
</article>
"""
                    else:
                        # Project is a dictionary
                        name = proj.get('name', '') or proj.get('project_name', '')
                        description = proj.get('description', '')
                        technologies = proj.get('technologies', [])
                        client = proj.get('client', '')
                        responsibilities = proj.get('responsibilities', [])

                        # Use Roman numerals for project numbering
                        roman_idx = KaniniResumeRenderer._to_roman(idx)
                        proj_html += f"""<article class="project">
<div class="project-title">Project {roman_idx}:</div>
<p><strong>{html_escape.escape(str(name))}</strong></p>
"""
                        if client:
                            proj_html += f"<p><strong>Client:</strong> {html_escape.escape(str(client))}</p>\n"
                        if technologies:
                            if isinstance(technologies, (list, tuple)):
                                tech_str = ", ".join(str(t) for t in technologies)
                            else:
                                tech_str = str(technologies)
                            proj_html += f"<p><strong>Technologies:</strong> {html_escape.escape(tech_str)}</p>\n"
                        if description:
                            proj_html += f"<p>{html_escape.escape(str(description))}</p>\n"
                        if responsibilities:
                            proj_html += """<div class="responsibilities-title">Roles and Responsibilities:</div>
<ul>
"""
                            for resp in responsibilities:
                                proj_html += f"<li>{html_escape.escape(str(resp))}</li>\n"
                            proj_html += "</ul>\n"

                        proj_html += "</article>\n"

            proj_html += "</section>"
            sections.append(proj_html)

        # Education
        if education:
            edu_html = """<section class="resume-section">
<h2>Educational Qualification</h2>
<ul>
"""
            for edu in education:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                year = edu.get('year', '')
                gpa = edu.get('gpa', '')

                edu_parts = []
                if degree:
                    edu_parts.append(str(degree))
                if year:
                    edu_parts.append(f"({year})")
                if institution:
                    edu_parts.append(f"from {institution}")
                if gpa:
                    edu_parts.append(f"GPA: {gpa}")

                edu_line = " ".join(edu_parts)
                edu_html += f"<li>{html_escape.escape(edu_line)}</li>\n"

            edu_html += """</ul>
</section>"""
            sections.append(edu_html)

        # Certifications
        if certifications:
            if isinstance(certifications, str):
                cert_list = [line.strip() for line in certifications.strip().split('\n') if line.strip()]
            else:
                cert_list = certifications if isinstance(certifications, list) else [certifications]

            cert_html = """<section class="resume-section">
<h2>Certifications</h2>
<ul>
"""
            for cert in cert_list:
                cert_html += f"<li>{html_escape.escape(str(cert))}</li>\n"

            cert_html += """</ul>
</section>"""
            sections.append(cert_html)

        # Achievements
        if achievements:
            if isinstance(achievements, str):
                ach_list = [line.strip() for line in achievements.strip().split('\n') if line.strip()]
            else:
                ach_list = achievements if isinstance(achievements, list) else [achievements]

            ach_html = """<section class="resume-section">
<h2>Achievements</h2>
<ul>
"""
            for ach in ach_list:
                ach_html += f"<li>{html_escape.escape(str(ach))}</li>\n"

            ach_html += """</ul>
</section>"""
            sections.append(ach_html)

        # Assemble full HTML
        name = html_escape.escape(str(contact.get("name", "CANDIDATE NAME"))).upper()
        sections_str = "\n".join(sections)
        
        # Only include contact HTML if it has content (personal details removed)
        contact_section = f'<p class="resume-contact">{contact_html}</p>' if contact_html.strip() else ''

        # Add logo to HTML preview
        logo_html = ""
        logo_path = Path(__file__).resolve().parent.parent.parent / "kanini_logo.png"
        if logo_path.exists():
            try:
                import base64
                with open(logo_path, 'rb') as f:
                    logo_base64 = base64.b64encode(f.read()).decode('utf-8')
                    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="kanini-logo" alt="Kanini Logo">'
            except Exception:
                pass  # Logo optional

        full_html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
{css}
</style>
</head>
<body>
<main class="resume-page">
{logo_html}
<h1 class="resume-name">{name}</h1>
{contact_section}
{sections_str}
</main>
</body>
</html>"""

        return full_html

    @staticmethod
    def _to_roman(num: int) -> str:
        """Convert number to Roman numeral."""
        values = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
        result = ""
        for value, symbol in values:
            while num >= value:
                result += symbol
                num -= value
        return result

    @staticmethod
    def _safe_text(text: Any) -> str:
        """Safely convert text to string, handling None and special characters."""
        if text is None:
            return ""
        text = str(text).strip()
        # Escape special XML characters for reportlab
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text

    @staticmethod
    async def render_pdf(resume_data: Dict[str, Any], template_id: str = "template1") -> bytes:
        """Render the exact HTML preview as an in-memory PDF."""
        from playwright.async_api import async_playwright

        preview_html = KaniniResumeRenderer.render_html(resume_data, template_id)
        pdf_page_rules = "@page :first { margin-top: 0; }"
        if template_id == "template1":
            pdf_page_rules += (
                ".resume-section { break-inside: auto; }"
                ".resume-section > h2 { break-after: avoid; }"
            )
        preview_html = preview_html.replace(
            "</style>",
            f"{pdf_page_rules}</style>",
            1,
        )
        logo_match = re.search(r'<img src="([^"]+)" class="kanini-logo"[^>]*>', preview_html)
        header_template = "<div></div>"
        if logo_match:
            preview_html = preview_html.replace(logo_match.group(0), "", 1)
            header_template = (
                '<div style="width:100%; padding:18px 0 0 36px; box-sizing:border-box;">'
                f'<img src="{logo_match.group(1)}" style="width:2cm; height:auto;">'
                '</div>'
            )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await page.set_content(preview_html, wait_until="load")
                return await page.pdf(
                    prefer_css_page_size=True,
                    print_background=True,
                    display_header_footer=True,
                    header_template=header_template,
                    footer_template="<div></div>",
                    margin={"top": "0.65in", "right": "0", "bottom": "0", "left": "0"},
                )
            finally:
                await browser.close()

        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.utils import ImageReader
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            from io import BytesIO
            
            # Create PDF in memory
            pdf_buffer = BytesIO()
            
            # Set page size based on template
            page_size = A4 if template_id == "template2" else letter
            margins = 1 * inch
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=page_size,
                leftMargin=margins,
                rightMargin=margins,
                topMargin=margins,
                bottomMargin=margins,
            )
            
            # Create styles
            styles = getSampleStyleSheet()
            
            # Custom styles matching Kanini design
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor='black',
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=11,
                textColor='black',
                spaceAfter=4,
                spaceBefore=8,
                fontName='Helvetica-Bold',
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=4,
            )
            
            # Draw the same compact header logo as DOCX on every PDF page.
            logo_path = Path(__file__).resolve().parent.parent.parent / "kanini_logo.png"
            logo_image = None
            if logo_path.exists():
                try:
                    logo_image = ImageReader(str(logo_path))
                except Exception:
                    pass

            def draw_logo(canvas, document):
                if logo_image is None:
                    return
                logo_size = cm * 2
                canvas.drawImage(
                    logo_image,
                    document.leftMargin - 10,
                    document.pagesize[1] - document.topMargin + 10,
                    width=logo_size,
                    height=logo_size,
                    mask='auto',
                )

            # Build content
            content = []
            
            # Add name
            contact = resume_data.get("contact", {})
            name = KaniniResumeRenderer._safe_text(contact.get("name", "CANDIDATE NAME")).upper()
            content.append(Paragraph(name, title_style))
            content.append(Spacer(1, 0.2 * inch))
            
            # Profile Summary
            summary = resume_data.get("summary", "")
            if summary:
                content.append(Paragraph("PROFILE SUMMARY", heading_style))
                summary_lines = [line.strip() for line in str(summary).strip().split('\n') if line.strip()]
                for line in summary_lines:
                    safe_line = KaniniResumeRenderer._safe_text(line)
                    content.append(Paragraph(f"• {safe_line}", body_style))
                content.append(Spacer(1, 0.1 * inch))
            
            # Technical Skills
            skills = resume_data.get("skills", {})
            if skills:
                content.append(Paragraph("TECHNICAL SKILLS", heading_style))
                if isinstance(skills, dict):
                    for category, skill_list in skills.items():
                        if isinstance(skill_list, (list, tuple)):
                            skills_text = ", ".join(KaniniResumeRenderer._safe_text(s) for s in skill_list)
                        else:
                            skills_text = KaniniResumeRenderer._safe_text(skill_list)
                        safe_category = KaniniResumeRenderer._safe_text(category)
                        content.append(Paragraph(f"<b>{safe_category}:</b> {skills_text}", body_style))
                elif isinstance(skills, str):
                    skill_lines = [line.strip() for line in str(skills).strip().split('\n') if line.strip()]
                    for line in skill_lines:
                        safe_line = KaniniResumeRenderer._safe_text(line)
                        content.append(Paragraph(f"• {safe_line}", body_style))
                content.append(Spacer(1, 0.1 * inch))
            
            # Work Experience
            experience = resume_data.get("experience", [])
            if experience:
                content.append(Paragraph("WORK EXPERIENCE", heading_style))
                for exp in experience:
                    title = KaniniResumeRenderer._safe_text(exp.get('title', '') or exp.get('job_title', ''))
                    company = KaniniResumeRenderer._safe_text(exp.get('company', '') or exp.get('company_name', ''))
                    dates = KaniniResumeRenderer._safe_text(exp.get('dates', ''))
                    responsibilities = exp.get('responsibilities', [])
                    
                    if title:
                        content.append(Paragraph(f"<b>{title}</b>", body_style))
                    if company or dates:
                        content.append(Paragraph(f"{company} | {dates}", body_style))
                    
                    if responsibilities:
                        for resp in responsibilities:
                            safe_resp = KaniniResumeRenderer._safe_text(resp)
                            content.append(Paragraph(f"• {safe_resp}", body_style))
                    content.append(Spacer(1, 0.05 * inch))
                content.append(Spacer(1, 0.1 * inch))
            
            # Education
            education = resume_data.get("education", [])
            if education:
                content.append(Paragraph("EDUCATION", heading_style))
                for edu in education:
                    degree = KaniniResumeRenderer._safe_text(edu.get('degree', ''))
                    school = KaniniResumeRenderer._safe_text(edu.get('school', '') or edu.get('institution', ''))
                    year = KaniniResumeRenderer._safe_text(edu.get('year', '') or edu.get('graduation_year', ''))
                    
                    if degree:
                        content.append(Paragraph(f"<b>{degree}</b>", body_style))
                    if school or year:
                        content.append(Paragraph(f"{school} | {year}", body_style))
                content.append(Spacer(1, 0.1 * inch))
            
            # Projects
            projects = resume_data.get("projects", [])
            if projects:
                content.append(Paragraph("PROJECTS", heading_style))
                if isinstance(projects, str):
                    # Handle projects as a single string with line breaks
                    proj_list = [line.strip() for line in str(projects).strip().split('\n') if line.strip()]
                    for proj_text in proj_list:
                        content.append(Paragraph(KaniniResumeRenderer._safe_text(proj_text), body_style))
                else:
                    # Handle projects as a list
                    for proj in projects:
                        if isinstance(proj, str):
                            # Project is a string
                            content.append(Paragraph(KaniniResumeRenderer._safe_text(proj), body_style))
                        else:
                            # Project is a dictionary
                            proj_title = KaniniResumeRenderer._safe_text(proj.get('title', '') or proj.get('name', ''))
                            proj_desc = KaniniResumeRenderer._safe_text(proj.get('description', ''))
                            
                            if proj_title:
                                content.append(Paragraph(f"<b>{proj_title}</b>", body_style))
                            if proj_desc:
                                content.append(Paragraph(proj_desc, body_style))
                content.append(Spacer(1, 0.1 * inch))
            
            # Certifications
            certifications = resume_data.get("certifications", [])
            if certifications:
                content.append(Paragraph("CERTIFICATIONS", heading_style))
                if isinstance(certifications, str):
                    # Handle certifications as a single string with line breaks
                    cert_list = [line.strip() for line in str(certifications).strip().split('\n') if line.strip()]
                    for cert_name in cert_list:
                        content.append(Paragraph(f"• {KaniniResumeRenderer._safe_text(cert_name)}", body_style))
                else:
                    # Handle certifications as a list
                    for cert in certifications:
                        if isinstance(cert, str):
                            # Cert is a string
                            cert_name = KaniniResumeRenderer._safe_text(cert)
                        else:
                            # Cert is a dictionary
                            cert_name = KaniniResumeRenderer._safe_text(cert.get('name', '') or cert.get('title', ''))
                        if cert_name:
                            content.append(Paragraph(f"• {cert_name}", body_style))
                content.append(Spacer(1, 0.1 * inch))
            
            # Achievements
            achievements = resume_data.get("achievements", [])
            if achievements:
                content.append(Paragraph("ACHIEVEMENTS", heading_style))
                if isinstance(achievements, str):
                    ach_list = [line.strip() for line in str(achievements).strip().split('\n') if line.strip()]
                else:
                    ach_list = achievements if isinstance(achievements, list) else [achievements]
                
                for ach in ach_list:
                    safe_ach = KaniniResumeRenderer._safe_text(ach)
                    if safe_ach:
                        content.append(Paragraph(f"• {safe_ach}", body_style))
            
            # Build PDF - ensure content is not empty
            if not content:
                content.append(Paragraph("Resume content could not be generated", body_style))
            
            doc.build(content, onFirstPage=draw_logo, onLaterPages=draw_logo)
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except ImportError as e:
            raise Exception(f"reportlab not installed: {e}")
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")

    @staticmethod
    def render_docx(resume_data: Dict[str, Any], template_id: str = "template1") -> bytes:
        """Render resume as DOCX using python-docx with Kanini logo."""
        try:
            from docx import Document
            from docx.shared import Pt, Inches, RGBColor, Cm
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

            doc = Document()
            
            # Add logo to header - positioned top-left with reduced size (1.5cm)
            section = doc.sections[0]
            header = section.header
            header.paragraphs[0].paragraph_format.space_before = Pt(0)
            header.paragraphs[0].paragraph_format.space_after = Pt(0)
            header.paragraphs[0].paragraph_format.line_spacing = 1.0
            header.paragraphs[0].paragraph_format.left_indent = Cm(-0.5)  # Move left
            
            logo_path = Path(__file__).resolve().parent.parent.parent / "kanini_logo.png"
            if logo_path.exists():
                try:
                    # Add logo with slightly larger size (2cm for better visibility)
                    run = header.paragraphs[0].add_run()
                    run.add_picture(str(logo_path), width=Cm(2))  # Increased from 1.5cm
                except Exception as e:
                    pass  # Logo optional
            
            contact = resume_data.get("contact", {})
            name = contact.get("name", "CANDIDATE NAME")

            # Add name - uppercase, bold, centered, black color
            name_para = doc.add_paragraph()
            name_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            name_run = name_para.add_run(name.upper())
            name_run.font.size = Pt(12)
            name_run.font.bold = True
            name_run.font.color.rgb = RGBColor(0, 0, 0)  # Black
            
            # NO PERSONAL DETAILS - Skip phone, email, location, linkedin, github

            # Summary
            if resume_data.get("summary"):
                heading = doc.add_heading("PROFILE SUMMARY", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                for line in resume_data["summary"].strip().split('\n'):
                    if line.strip():
                        doc.add_paragraph(line.strip(), style='List Bullet')

            # Skills
            if resume_data.get("skills"):
                heading = doc.add_heading("TECHNICAL SKILLS", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                skills = resume_data["skills"]
                if isinstance(skills, dict):
                    for category, skill_list in skills.items():
                        if isinstance(skill_list, (list, tuple)):
                            skills_str = ", ".join(str(s) for s in skill_list)
                        else:
                            skills_str = str(skill_list)
                        p = doc.add_paragraph(style='List Bullet')
                        p_run = p.add_run(f"{category}: ")
                        p_run.bold = True
                        p_run.font.color.rgb = RGBColor(0, 0, 0)
                        p.add_run(skills_str)

            # Experience
            if resume_data.get("experience"):
                heading = doc.add_heading("WORK EXPERIENCE", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                for exp in resume_data["experience"]:
                    title = exp.get('title', '') or exp.get('job_title', '')
                    company = exp.get('company', '') or exp.get('company_name', '')
                    dates = exp.get('dates', '')

                    # Add company info with bold formatting and black color
                    p = doc.add_paragraph()
                    p_run = p.add_run("Company Name: ")
                    p_run.bold = True
                    p_run.font.color.rgb = RGBColor(0, 0, 0)
                    p.add_run(company)

                    p = doc.add_paragraph()
                    p_run = p.add_run("Designation: ")
                    p_run.bold = True
                    p_run.font.color.rgb = RGBColor(0, 0, 0)
                    p.add_run(title)

                    p = doc.add_paragraph()
                    p_run = p.add_run("Duration: ")
                    p_run.bold = True
                    p_run.font.color.rgb = RGBColor(0, 0, 0)
                    p.add_run(dates)

                    if exp.get('responsibilities'):
                        for resp in exp['responsibilities']:
                            doc.add_paragraph(str(resp), style='List Bullet')

            # Projects
            if resume_data.get("projects"):
                heading = doc.add_heading("PROJECT SUMMARY", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                for idx, proj in enumerate(resume_data["projects"], 1):
                    roman_idx = KaniniResumeRenderer._to_roman(idx)
                    name_proj = proj.get('name', '') or proj.get('project_name', '')
                    
                    p = doc.add_paragraph()
                    p_run = p.add_run(f"Project {roman_idx}: {name_proj}")
                    p_run.bold = True
                    p_run.font.color.rgb = RGBColor(0, 0, 0)

                    if proj.get('client'):
                        p = doc.add_paragraph()
                        p_run = p.add_run("Client: ")
                        p_run.bold = True
                        p_run.font.color.rgb = RGBColor(0, 0, 0)
                        p.add_run(str(proj['client']))
                    
                    if proj.get('technologies'):
                        tech_str = ", ".join(proj['technologies']) if isinstance(proj['technologies'], list) else str(proj['technologies'])
                        p = doc.add_paragraph()
                        p_run = p.add_run("Technologies: ")
                        p_run.bold = True
                        p_run.font.color.rgb = RGBColor(0, 0, 0)
                        p.add_run(tech_str)

                    if proj.get('description'):
                        doc.add_paragraph(str(proj['description']))

                    if proj.get('responsibilities'):
                        p = doc.add_paragraph()
                        p_run = p.add_run("Roles and Responsibilities:")
                        p_run.bold = True
                        p_run.font.color.rgb = RGBColor(0, 0, 0)
                        for resp in proj['responsibilities']:
                            doc.add_paragraph(str(resp), style='List Bullet')

            # Education
            if resume_data.get("education"):
                heading = doc.add_heading("EDUCATIONAL QUALIFICATION", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                for edu in resume_data["education"]:
                    degree = edu.get('degree', '')
                    institution = edu.get('institution', '')
                    year = edu.get('year', '')
                    gpa = edu.get('gpa', '')

                    edu_text = f"{degree}"
                    if year:
                        edu_text += f" ({year})"
                    if institution:
                        edu_text += f" from {institution}"
                    if gpa:
                        edu_text += f" - GPA: {gpa}"

                    doc.add_paragraph(edu_text, style='List Bullet')

            # Certifications
            if resume_data.get("certifications"):
                heading = doc.add_heading("CERTIFICATIONS", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                certs = resume_data["certifications"]
                cert_list = certs.split('\n') if isinstance(certs, str) else certs if isinstance(certs, list) else [certs]
                for cert in cert_list:
                    if str(cert).strip():
                        doc.add_paragraph(str(cert).strip(), style='List Bullet')

            # Achievements
            if resume_data.get("achievements"):
                heading = doc.add_heading("ACHIEVEMENTS", level=2)
                heading_format = heading.runs[0]
                heading_format.font.color.rgb = RGBColor(0, 0, 0)  # Black
                achs = resume_data["achievements"]
                ach_list = achs.split('\n') if isinstance(achs, str) else achs if isinstance(achs, list) else [achs]
                for ach in ach_list:
                    if str(ach).strip():
                        doc.add_paragraph(str(ach).strip(), style='List Bullet')

            # Save to bytes
            from io import BytesIO
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            return output.getvalue()

        except ImportError:
            # If docx not available, return empty bytes
            return b""
