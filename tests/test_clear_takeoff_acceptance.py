"""Shared behavioral contract for both Clear Takeoff runs.

Tests use the public batch builder and a fake model client, not extractor internals.
"""
import json
from pathlib import Path

import pytest

from vehicle_accidents_extractor.artifact_paths import ArtifactPaths
from vehicle_accidents_extractor.batch.accident_batch_extractor import AccidentBatchExtractorBuilder
from vehicle_accidents_extractor.input_paths import InputPaths
from vehicle_accidents_extractor.llm.config import Config
from vehicle_accidents_extractor.llm.llm_client import LLMAttempt, LLMResult


VALID_ACCIDENT = {
    "accident_type": "rear_end",
    "weather": ["clear"],
    "road_surface": "dry",
    "lighting": "daylight",
    "location_type": "non_junction",
    "area_type": ["urban"],
    "speed_limit_mph": 30,
    "vehicles": [
        {"label": "V1", "year": None, "make": None, "model": None, "towed": None}
    ],
    "injuries_reported": False,
    "critical_reason": None,
}


def model_reply(content=None, *, finish_reason="stop", error=None):
    return LLMResult(
        content=content,
        finish_reason=finish_reason,
        attempts=(LLMAttempt("ok" if error is None else "APIError", 0.01, 8, 10, error),),
        error=error,
    )


class FakeLLM:
    """Return predetermined responses and record each logical model call."""

    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def call(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.replies)


def extract_record(tmp_path: Path, responses):
    batch = tmp_path / "data" / "batches" / "trial" / "texts"
    batch.mkdir(parents=True)
    (batch / "case-1.txt").write_text(
        "Car V1 rear-ended another car in daylight on a dry city road.",
        encoding="utf-8",
    )
    prompts = tmp_path / "prompts" / "v1"
    prompts.mkdir(parents=True)
    (prompts / "system.txt").write_text("Return JSON matching the schema.", encoding="utf-8")
    (prompts / "repair.txt").write_text("Fix the JSON: {error}", encoding="utf-8")

    config = Config.model_validate(
        {
            "timeout_seconds": 10,
            "max_retries": 0,
            "max_tokens": 800,
            "models": {
                "fake": {
                    "base_url": "http://localhost:1234/v1",
                    "model": "fake",
                    "price_per_1m": [0.0, 0.0],
                }
            },
            "sampling": {"fixed": {"temperature": 0, "top_p": 1}},
        }
    )
    fake = FakeLLM(responses)
    runner = (
        AccidentBatchExtractorBuilder(config, InputPaths(tmp_path))
        .for_accident_batch("trial")
        .with_model_profile("fake")
        .with_llm_client(fake)
        .with_prompt_version("v1")
        .with_sampling_profile("fixed")
        .saving_records_to(ArtifactPaths(tmp_path))
        .build()
    )
    assert runner.extract() == 1
    lines = runner.extraction_run_records_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["accident_id"] == "case-1"
    return record, fake


def test_valid_first_reply(tmp_path):
    record, fake = extract_record(tmp_path, [model_reply(json.dumps(VALID_ACCIDENT))])
    assert record["status"] == "valid"
    assert record["accident"]["accident_type"] == "rear_end"
    assert record["repair_attempted"] is False
    assert len(record["calls"]) == len(fake.calls) == 1


def test_invalid_json_then_repair(tmp_path):
    record, fake = extract_record(
        tmp_path, [model_reply("{broken"), model_reply(json.dumps(VALID_ACCIDENT))]
    )
    assert record["status"] == "repaired"
    assert record["repair_attempted"] is True
    assert len(record["calls"]) == len(fake.calls) == 2
    assert len(record["validation_errors"]) == 1


def test_invalid_twice_fails(tmp_path):
    record, fake = extract_record(tmp_path, [model_reply("{bad"), model_reply("{bad")])
    assert record["status"] == "failed"
    assert record["accident"] is None
    assert record["repair_attempted"] is True
    assert len(record["calls"]) == len(fake.calls) == 2
    assert len(record["validation_errors"]) == 2


@pytest.mark.parametrize(
    "response",
    [
        model_reply(error="API failure", finish_reason=None),
        model_reply(content=None, finish_reason="content_filter", error="refused"),
    ],
)
def test_unrepairable_response_does_not_retry(tmp_path, response):
    record, fake = extract_record(tmp_path, [response])
    assert record["status"] == "failed"
    assert record["repair_attempted"] is False
    assert len(record["calls"]) == len(fake.calls) == 1


def test_truncated_reply_gets_one_repair(tmp_path):
    record, fake = extract_record(
        tmp_path,
        [
            model_reply('{"accident_type":', finish_reason="length"),
            model_reply(json.dumps(VALID_ACCIDENT)),
        ],
    )
    assert record["status"] == "repaired"
    assert record["repair_attempted"] is True
    assert len(record["calls"]) == len(fake.calls) == 2
