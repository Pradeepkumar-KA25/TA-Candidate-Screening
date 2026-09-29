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