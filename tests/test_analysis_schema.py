"""Tests for LLM analysis Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.core.news_constants import NewsEventCategory
from app.schemas.analysis import AnalysisTimeHorizon, CategoryScores, LLMNewsAnalysisOutput
from tests.helpers.analysis import make_valid_llm_output


def test_valid_structured_result() -> None:
    output = make_valid_llm_output()
    assert output.event_type == NewsEventCategory.SANCTIONS
    assert -1.0 <= output.direction_usd_irr <= 1.0
    assert 0.0 <= output.impact_score <= 10.0


def test_invalid_direction_range() -> None:
    with pytest.raises(ValidationError):
        make_valid_llm_output(direction_usd_irr=1.5)


def test_invalid_impact_score() -> None:
    with pytest.raises(ValidationError):
        make_valid_llm_output(impact_score=11.0)


def test_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        make_valid_llm_output(content_confidence=1.5)


def test_no_buy_sell_field_in_schema() -> None:
    forbidden = LLMNewsAnalysisOutput.forbidden_output_fields()
    assert "buy" in forbidden
    assert "sell" in forbidden
    assert "source_reliability" in forbidden
    fields = set(LLMNewsAnalysisOutput.model_fields.keys())
    assert fields.isdisjoint(forbidden)


def test_source_reliability_not_in_schema() -> None:
    assert "source_reliability" not in LLMNewsAnalysisOutput.model_fields


def test_category_scores_validation() -> None:
    with pytest.raises(ValidationError):
        CategoryScores(
            military=-1.0,
            sanctions=0.0,
            negotiation=0.0,
            oil_export=0.0,
            fx_policy=0.0,
            monetary=0.0,
            inflation=0.0,
            foreign_reserves=0.0,
            regional_risk=0.0,
        )


def test_malformed_json_schema_validation() -> None:
    with pytest.raises(ValidationError):
        LLMNewsAnalysisOutput.model_validate({"summary": "only partial"})


def test_time_horizon_enum() -> None:
    output = make_valid_llm_output(time_horizon=AnalysisTimeHorizon.INTRADAY)
    assert output.time_horizon == AnalysisTimeHorizon.INTRADAY
