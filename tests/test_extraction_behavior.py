"""Test extraction behavior through its public interfaces."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from openai import APIConnectionError, OpenAIError

from vehicle_accidents_extractor.evaluation.accident_extraction_scorer import (
    score_accident,
)
from vehicle_accidents_extractor.extraction.response_validator import (
    ResponseValidator,
    UnrepairableResponse,
)
from vehicle_accidents_extractor.llm.config import ModelConfig
from vehicle_accidents_extractor.llm.llm_client import (
    LLMClient,
    LLMResult,
)
from vehicle_accidents_extractor.schema import VehicleAccident


VALID_ACCIDENT_JSON = """{
  "accident_type": "rear_end",
  "weather": [],
  "road_surface": null,
  "lighting": null,
  "location_type": null,
  "area_type": [],
  "speed_limit_mph": 35,
  "vehicles": [],
  "injuries_reported": null,
  "critical_reason": null
}"""


class FakeOpenAIClient:
    """Stand in for the external SDK at LLMClient's injected seam."""

    def __init__(self, responses):
        self._responses = iter(responses)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create_completion),
        )

    def with_options(self, **_options):
        return self

    def close(self):
        pass

    def _create_completion(self, **_request):
        response = next(self._responses)
        if isinstance(response, Exception):
            raise response
        return response


def completion(content: str):
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8),
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=content, refusal=None),
            finish_reason="stop",
        )],
    )


def accident_with_vehicles(vehicles: list[dict]) -> VehicleAccident:
    return VehicleAccident(
        accident_type=None,
        weather=[],
        road_surface=None,
        lighting=None,
        location_type=None,
        area_type=[],
        speed_limit_mph=None,
        vehicles=vehicles,
        injuries_reported=None,
        critical_reason=None,
    )


class ExtractionBehaviorTests(unittest.TestCase):
    def test_valid_json(self):
        result = LLMResult(VALID_ACCIDENT_JSON, "stop", ())

        accident = ResponseValidator(VehicleAccident).validate(result)

        self.assertEqual(accident.speed_limit_mph, 35)

    def test_invalid_json_repairable(self):
        result = LLMResult("{", "stop", ())

        with self.assertRaises(ValueError):
            ResponseValidator(VehicleAccident).validate(result)

    def test_api_failure_unrepairable(self):
        result = LLMResult(None, None, (), error="BadRequestError: invalid request")

        with self.assertRaises(UnrepairableResponse):
            ResponseValidator(VehicleAccident).validate(result)

    def test_connection_failure_retries_once(self):
        connection_error = APIConnectionError(
            message="connection lost",
            request=SimpleNamespace(url="https://example.test/v1/chat/completions"),
        )
        sdk_client = FakeOpenAIClient([connection_error, completion(VALID_ACCIDENT_JSON)])
        llm_client = LLMClient(
            base_url="https://example.test/v1",
            api_key="test-key",
            model="test-model",
            timeout_seconds=1,
            max_retries=1,
            openai_client=sdk_client,
        )

        with llm_client, patch("vehicle_accidents_extractor.llm.llm_client.time.sleep") as sleep:
            result = llm_client.call(
                messages=[], temperature=0, top_p=1, max_tokens=10, response_format={},
            )

        self.assertTrue(result.has_content)
        self.assertEqual([attempt.outcome for attempt in result.attempts], [
            "APIConnectionError", "ok",
        ])
        sleep.assert_called_once_with(1)

    def test_bad_request_no_retry(self):
        sdk_client = FakeOpenAIClient([OpenAIError("invalid request")])
        llm_client = LLMClient(
            base_url="https://example.test/v1",
            api_key="test-key",
            model="test-model",
            timeout_seconds=1,
            max_retries=2,
            openai_client=sdk_client,
        )

        with llm_client, patch("vehicle_accidents_extractor.llm.llm_client.time.sleep") as sleep:
            result = llm_client.call(
                messages=[], temperature=0, top_p=1, max_tokens=10, response_format={},
            )

        self.assertFalse(result.has_content)
        self.assertEqual(len(result.attempts), 1)
        sleep.assert_not_called()

    def test_vehicle_order_invariant(self):
        golden_vehicles = [
            {"label": None, "year": None, "make": "Ford", "model": "Focus", "towed": None},
            {"label": None, "year": None, "make": "Honda", "model": "Civic", "towed": None},
        ]
        extracted_vehicles = [
            {"label": None, "year": None, "make": "Ford", "model": "Civic", "towed": None},
            {"label": None, "year": None, "make": "Honda", "model": "Focus", "towed": None},
        ]

        forward = score_accident(
            accident_with_vehicles(golden_vehicles),
            accident_with_vehicles(extracted_vehicles),
        )
        reversed_lists = score_accident(
            accident_with_vehicles(list(reversed(golden_vehicles))),
            accident_with_vehicles(list(reversed(extracted_vehicles))),
        )

        self.assertEqual(forward.correct, reversed_lists.correct)
        self.assertEqual(forward.total, reversed_lists.total)
        self.assertEqual(forward.by_field, reversed_lists.by_field)
        self.assertEqual(forward.mismatches, reversed_lists.mismatches)

    def test_llm_base_url(self):
        llm_client = LLMClient(
            base_url="https://example.test/v1",
            api_key="test-key",
            model="test-model",
            timeout_seconds=1,
            max_retries=0,
            openai_client=FakeOpenAIClient([]),
        )

        with llm_client:
            self.assertEqual(llm_client.base_url, "https://example.test/v1")

    def test_model_session_pair(self):
        from vehicle_accidents_extractor.batch.model_session import ModelSession

        model_config = ModelConfig(
            base_url="https://example.test/v1",
            api_key_env="TEST_API_KEY",
            model="configured-model",
            price_per_1m=(0, 0),
        )
        llm_client = LLMClient(
            base_url=model_config.base_url,
            api_key="test-key",
            model=model_config.model,
            timeout_seconds=1,
            max_retries=0,
            openai_client=FakeOpenAIClient([]),
        )

        with llm_client:
            model_session = ModelSession("provider", model_config, llm_client)

        self.assertEqual(model_session.model_profile, "provider")
        self.assertEqual(model_session.model_config, model_config)
        self.assertIs(model_session.llm_client, llm_client)

    def test_session_rejects_model_mismatch(self):
        from vehicle_accidents_extractor.batch.model_session import ModelSession

        model_config = ModelConfig(
            base_url="https://example.test/v1",
            api_key_env="TEST_API_KEY",
            model="configured-model",
            price_per_1m=(0, 0),
        )
        llm_client = LLMClient(
            base_url=model_config.base_url,
            api_key="test-key",
            model="different-model",
            timeout_seconds=1,
            max_retries=0,
            openai_client=FakeOpenAIClient([]),
        )

        with llm_client, self.assertRaisesRegex(ValueError, "model"):
            ModelSession("provider", model_config, llm_client)

    def test_session_rejects_url_mismatch(self):
        from vehicle_accidents_extractor.batch.model_session import ModelSession

        model_config = ModelConfig(
            base_url="https://example.test/v1",
            api_key_env="TEST_API_KEY",
            model="configured-model",
            price_per_1m=(0, 0),
        )
        llm_client = LLMClient(
            base_url="https://other.example.test/v1",
            api_key="test-key",
            model=model_config.model,
            timeout_seconds=1,
            max_retries=0,
            openai_client=FakeOpenAIClient([]),
        )

        with llm_client, self.assertRaisesRegex(ValueError, "base URL"):
            ModelSession("provider", model_config, llm_client)


if __name__ == "__main__":
    unittest.main()
