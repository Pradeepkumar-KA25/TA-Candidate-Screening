from __future__ import annotations

from pydantic import ValidationError
import pytest

from app.schemas.ranking_criteria import (
    RankingCriteriaItemRequest,
    SetRankingCriteriaRequest,
)


class TestRankingCriteriaItemRequest:
    """Tests for individual ranking criteria item validation."""

    def test_valid_single_criterion(self) -> None:
        """Test creating a valid single criterion."""
        item = RankingCriteriaItemRequest(
            criteria_name="Technical Skills",
            weight_points=50.0,
        )
        assert item.criteria_name == "Technical Skills"
        assert item.weight_points == 50.0

    def test_normalizes_criteria_name_whitespace(self) -> None:
        """Test that criteria names are stripped of leading/trailing whitespace."""
        item = RankingCriteriaItemRequest(
            criteria_name="  Technical Skills  ",
            weight_points=50.0,
        )
        assert item.criteria_name == "Technical Skills"

    def test_rejects_empty_criteria_name(self) -> None:
        """Test that empty criteria names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RankingCriteriaItemRequest(
                criteria_name="",
                weight_points=50.0,
            )
        assert "string_too_short" in str(exc_info.value)

    def test_rejects_whitespace_only_criteria_name(self) -> None:
        """Test that whitespace-only criteria names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RankingCriteriaItemRequest(
                criteria_name="   ",
                weight_points=50.0,
            )
        assert "Criteria name is required" in str(exc_info.value)

    def test_rejects_zero_weight(self) -> None:
        """Test that zero weight is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RankingCriteriaItemRequest(
                criteria_name="Skills",
                weight_points=0.0,
            )
        assert "greater than 0" in str(exc_info.value)

    def test_rejects_negative_weight(self) -> None:
        """Test that negative weight is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RankingCriteriaItemRequest(
                criteria_name="Skills",
                weight_points=-10.0,
            )
        assert "greater than 0" in str(exc_info.value)

    def test_rejects_weight_over_100(self) -> None:
        """Test that weight over 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RankingCriteriaItemRequest(
                criteria_name="Skills",
                weight_points=101.0,
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_accepts_weight_exactly_100(self) -> None:
        """Test that weight of exactly 100 is accepted."""
        item = RankingCriteriaItemRequest(
            criteria_name="Skills",
            weight_points=100.0,
        )
        assert item.weight_points == 100.0

    def test_accepts_small_decimal_weight(self) -> None:
        """Test that small decimal weights are accepted."""
        item = RankingCriteriaItemRequest(
            criteria_name="Skills",
            weight_points=0.1,
        )
        assert item.weight_points == 0.1

    def test_rejects_max_length_criteria_name(self) -> None:
        """Test that criteria names exceeding max length are rejected."""
        long_name = "A" * 256  # exceeds max_length of 255
        with pytest.raises(ValidationError) as exc_info:
            RankingCriteriaItemRequest(
                criteria_name=long_name,
                weight_points=50.0,
            )
        assert "string_too_long" in str(exc_info.value)

    def test_accepts_max_length_criteria_name(self) -> None:
        """Test that criteria names at max length are accepted."""
        max_name = "A" * 255
        item = RankingCriteriaItemRequest(
            criteria_name=max_name,
            weight_points=50.0,
        )
        assert len(item.criteria_name) == 255


class TestSetRankingCriteriaRequest:
    """Tests for the full ranking criteria set request with weight validation."""

    def test_valid_criteria_sum_to_100(self) -> None:
        """Test that valid criteria summing to 100 are accepted."""
        request = SetRankingCriteriaRequest(
            criteria=[
                RankingCriteriaItemRequest(criteria_name="Skills", weight_points=40.0),
                RankingCriteriaItemRequest(criteria_name="Experience", weight_points=35.0),
                RankingCriteriaItemRequest(criteria_name="Fit", weight_points=25.0),
            ]
        )
        assert len(request.criteria) == 3
        assert sum(c.weight_points for c in request.criteria) == 100.0

    def test_rejects_criteria_sum_less_than_100(self) -> None:
        """Test that criteria summing to less than 100 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SetRankingCriteriaRequest(
                criteria=[
                    RankingCriteriaItemRequest(criteria_name="Skills", weight_points=40.0),
                    RankingCriteriaItemRequest(criteria_name="Experience", weight_points=35.0),
                ]
            )
        error_msg = str(exc_info.value)
        assert "100" in error_msg
        assert "75" in error_msg

    def test_rejects_criteria_sum_greater_than_100(self) -> None:
        """Test that criteria summing to more than 100 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SetRankingCriteriaRequest(
                criteria=[
                    RankingCriteriaItemRequest(criteria_name="Skills", weight_points=50.0),
                    RankingCriteriaItemRequest(criteria_name="Experience", weight_points=51.0),
                ]
            )
        error_msg = str(exc_info.value)
        assert "100" in error_msg
        assert "101" in error_msg

    def test_single_criterion_at_100(self) -> None:
        """Test that a single criterion can be 100 points."""
        request = SetRankingCriteriaRequest(
            criteria=[
                RankingCriteriaItemRequest(criteria_name="Overall Fit", weight_points=100.0),
            ]
        )
        assert len(request.criteria) == 1
        assert request.criteria[0].weight_points == 100.0

    def test_many_criteria_summing_to_100(self) -> None:
        """Test that many small criteria can sum to 100."""
        criteria = [
            RankingCriteriaItemRequest(criteria_name=f"Criterion {i}", weight_points=1.0)
            for i in range(100)
        ]
        request = SetRankingCriteriaRequest(criteria=criteria)
        assert len(request.criteria) == 100
        assert sum(c.weight_points for c in request.criteria) == 100.0

    def test_rejects_empty_criteria_list(self) -> None:
        """Test that empty criteria list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SetRankingCriteriaRequest(criteria=[])
        assert "too_short" in str(exc_info.value)

    def test_decimal_weights_sum_to_100(self) -> None:
        """Test that decimal weights summing to exactly 100 are accepted."""
        request = SetRankingCriteriaRequest(
            criteria=[
                RankingCriteriaItemRequest(criteria_name="Skills", weight_points=33.33),
                RankingCriteriaItemRequest(criteria_name="Experience", weight_points=33.33),
                RankingCriteriaItemRequest(criteria_name="Fit", weight_points=33.34),
            ]
        )
        total = sum(c.weight_points for c in request.criteria)
        assert abs(total - 100.0) < 0.01  # Allow for floating point rounding

    def test_rejects_criteria_sum_off_by_tiny_amount(self) -> None:
        """Test that even tiny deviations from 100 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SetRankingCriteriaRequest(
                criteria=[
                    RankingCriteriaItemRequest(criteria_name="Skills", weight_points=50.0),
                    RankingCriteriaItemRequest(criteria_name="Experience", weight_points=49.99),
                ]
            )
        assert "100" in str(exc_info.value)

    def test_accepts_criteria_with_various_decimal_places(self) -> None:
        """Test that criteria with various decimal places can sum to 100."""
        request = SetRankingCriteriaRequest(
            criteria=[
                RankingCriteriaItemRequest(criteria_name="Technical", weight_points=45.5),
                RankingCriteriaItemRequest(criteria_name="Experience", weight_points=30.25),
                RankingCriteriaItemRequest(criteria_name="Communication", weight_points=24.25),
            ]
        )
        total = sum(c.weight_points for c in request.criteria)
        assert total == 100.0

    def test_rejects_criteria_exceeding_max_count(self) -> None:
        """Test that criteria list exceeding max length is rejected."""
        criteria = [
            RankingCriteriaItemRequest(criteria_name=f"Criterion {i}", weight_points=0.01)
            for i in range(101)  # exceeds max_length of 100
        ]
        with pytest.raises(ValidationError) as exc_info:
            SetRankingCriteriaRequest(criteria=criteria)
        assert "too_long" in str(exc_info.value)
