from types import SimpleNamespace

from app.services.resume_enrichment_service import ResumeEnrichmentService


def test_compare_values_treats_empty_collections_as_empty() -> None:
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)

    assert service._compare_values([], ["Python"])['action'] == "PROPOSE_UPDATE"
    assert service._compare_values({}, "Professional summary")['action'] == "PROPOSE_UPDATE"


def test_compare_values_preserves_false_and_zero_as_existing_values() -> None:
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)

    assert service._compare_values(False, "resume value")['action'] == "KEEP_ZOHO"
    assert service._compare_values(0, "resume value")['action'] == "KEEP_ZOHO"


def test_resolve_zoho_field_uses_existing_raw_payload_key() -> None:
    payload = {
        "Skill_Set": "Python",
        "Highest_Qualification_Held": "MTech",
    }

    assert ResumeEnrichmentService._resolve_zoho_field(payload, ("Skills", "Skill_Set")) == (
        "Skill_Set",
        "Python",
    )
    assert ResumeEnrichmentService._resolve_zoho_field(
        payload, ("Highest_Qualification", "Highest_Qualification_Held")
    ) == ("Highest_Qualification_Held", "MTech")
    assert ResumeEnrichmentService._resolve_zoho_field(payload, ("Summary",)) is None


def test_current_experience_value_prefers_open_ended_role() -> None:
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)
    extracted_data = {
        "experience": [
            {"company": "Previous Employer", "title": "Engineer", "dates": "2019 - 2023"},
            {"company": "Current Employer", "title": "Lead Engineer", "dates": "2023 - Present"},
        ]
    }

    assert service._get_extracted_value(extracted_data, "experience.current.company") == "Current Employer"
    assert service._get_extracted_value(extracted_data, "experience.current.title") == "Lead Engineer"


def test_current_experience_value_uses_most_recent_dated_role_without_open_end() -> None:
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)
    extracted_data = {
        "experience": [
            {"company": "Older Employer", "dates": "2016 - 2020"},
            {"company": "Most Recent Employer", "dates": "2021 - 2025"},
        ]
    }

    assert service._get_extracted_value(extracted_data, "experience.current.company") == "Most Recent Employer"


def test_employment_fields_reject_prose_extraction_artifacts() -> None:
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)
    extracted_data = {
        "experience": [
            {
                "company": "Developed and maintained scalable data pipelines for reporting",
                "title": "Led and delivered cross-functional initiatives for enterprise clients",
                "dates": "2023 - Present",
            }
        ]
    }

    assert service._get_extracted_value(extracted_data, "experience.current.company") is None
    assert service._get_extracted_value(extracted_data, "experience.current.title") is None


def test_employment_fields_keep_concise_company_and_title_values() -> None:
    service = ResumeEnrichmentService.__new__(ResumeEnrichmentService)
    extracted_data = {
        "experience": [
            {
                "company": "Northwind Digital Solutions Pvt. Ltd.",
                "title": "Senior Data Engineer",
                "dates": "2023 - Present",
            }
        ]
    }

    assert service._get_extracted_value(extracted_data, "experience.current.company") == "Northwind Digital Solutions Pvt. Ltd."
    assert service._get_extracted_value(extracted_data, "experience.current.title") == "Senior Data Engineer"


def test_write_back_payload_contains_only_approved_empty_writable_fields() -> None:
    approved_changes = [
        SimpleNamespace(zoho_field_api_name="Phone", proposed_value="+1 555 0100"),
        SimpleNamespace(zoho_field_api_name="Email", proposed_value="new@example.com"),
        SimpleNamespace(zoho_field_api_name="Status", proposed_value="Active"),
    ]

    payload, skipped = ResumeEnrichmentService._build_candidate_update_payload(
        raw_payload={"Phone": None, "Email": "existing@example.com", "Status": None},
        approved_changes=approved_changes,
        writable_fields={"Phone", "Email"},
    )

    assert payload == {"Phone": "+1 555 0100"}
    assert {item["reason"] for item in skipped} == {
        "zoho_field_no_longer_empty",
        "field_not_writable",
    }


def test_approval_status_supports_partial_decisions() -> None:
    make_change = lambda status: SimpleNamespace(change_status=status)

    assert ResumeEnrichmentService._approval_status_for_changes(
        [make_change("APPROVED"), make_change("APPROVED")]
    ) == "APPROVED"
    assert ResumeEnrichmentService._approval_status_for_changes(
        [make_change("REJECTED"), make_change("REJECTED")]
    ) == "REJECTED"
    assert ResumeEnrichmentService._approval_status_for_changes(
        [make_change("APPROVED"), make_change("REJECTED")]
    ) == "PARTIALLY_APPROVED"
    assert ResumeEnrichmentService._approval_status_for_changes(
        [make_change("APPROVED"), make_change("PENDING")]
    ) == "PARTIALLY_APPROVED"
    assert ResumeEnrichmentService._approval_status_for_changes(
        [make_change("PENDING")]
    ) == "PENDING"