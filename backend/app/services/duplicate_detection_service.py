from __future__ import annotations

from dataclasses import dataclass
import re

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository


@dataclass(slots=True)
class DuplicateDetectionResult:
    scanned: int
    potential_duplicates: int
    created: int
    updated: int


@dataclass(slots=True)
class DuplicateDetectionService:
    candidate_repository: CandidateRepository
    duplicate_review_repository: DuplicateReviewRepository

    def detect(self) -> DuplicateDetectionResult:
        candidates = self.candidate_repository.list_all_for_duplicate_detection()
        created = 0
        updated = 0
        potential_duplicates = 0

        for index, left in enumerate(candidates):
            for right in candidates[index + 1 :]:
                decision = self._build_match_decision(left, right)
                if decision is None:
                    continue

                potential_duplicates += 1
                primary, secondary = self._ordered_pair(left.id, right.id)
                _, is_new = self.duplicate_review_repository.create_or_update_pending(
                    candidate_id=primary,
                    matched_candidate_id=secondary,
                    match_basis=decision["match_basis"],
                    confidence=decision["confidence"],
                    jd_id=None,
                )
                if is_new:
                    created += 1
                else:
                    updated += 1

        return DuplicateDetectionResult(
            scanned=len(candidates),
            potential_duplicates=potential_duplicates,
            created=created,
            updated=updated,
        )

    @staticmethod
    def _ordered_pair(left_id, right_id):
        return (left_id, right_id) if str(left_id) < str(right_id) else (right_id, left_id)

    def _build_match_decision(self, left, right) -> dict | None:
        left_email = self._normalize_email(left.email)
        right_email = self._normalize_email(right.email)
        left_phone = self._normalize_phone(left.phone)
        right_phone = self._normalize_phone(right.phone)

        email_exact = bool(left_email and right_email and left_email == right_email)
        phone_exact = bool(left_phone and right_phone and left_phone == right_phone)

        if email_exact and phone_exact:
            return {"match_basis": "email_exact+phone_exact", "confidence": 0.99}
        if email_exact:
            return {"match_basis": "email_exact", "confidence": 0.95}
        if phone_exact:
            return {"match_basis": "phone_exact", "confidence": 0.93}

        email_near = bool(left_email and right_email and self._emails_near_match(left_email, right_email))
        phone_near = bool(left_phone and right_phone and self._phones_near_match(left_phone, right_phone))

        if email_near and phone_near:
            return {"match_basis": "email_near+phone_near", "confidence": 0.88}
        if email_near:
            return {"match_basis": "email_near", "confidence": 0.82}
        if phone_near:
            return {"match_basis": "phone_near", "confidence": 0.78}

        return None

    @staticmethod
    def _normalize_email(value: str | None) -> str | None:
        if not value:
            return None
        text = value.strip().lower()
        return text or None

    @staticmethod
    def _normalize_phone(value: str | None) -> str | None:
        if not value:
            return None
        digits = re.sub(r"\D", "", value)
        if not digits:
            return None
        # Compare by last 10 digits to tolerate country code prefixes.
        return digits[-10:] if len(digits) >= 10 else digits

    @staticmethod
    def _emails_near_match(left_email: str, right_email: str) -> bool:
        left_local, left_domain = DuplicateDetectionService._split_email(left_email)
        right_local, right_domain = DuplicateDetectionService._split_email(right_email)
        if not left_local or not right_local or not left_domain or left_domain != right_domain:
            return False

        left_canonical = left_local.split("+", 1)[0].replace(".", "")
        right_canonical = right_local.split("+", 1)[0].replace(".", "")
        return left_canonical == right_canonical

    @staticmethod
    def _split_email(value: str) -> tuple[str | None, str | None]:
        if "@" not in value:
            return None, None
        local, domain = value.split("@", 1)
        local = local.strip()
        domain = domain.strip()
        if not local or not domain:
            return None, None
        return local, domain

    @staticmethod
    def _phones_near_match(left_phone: str, right_phone: str) -> bool:
        if len(left_phone) != len(right_phone):
            return False
        if left_phone == right_phone:
            return False

        differences = sum(1 for left, right in zip(left_phone, right_phone) if left != right)
        return differences <= 1
