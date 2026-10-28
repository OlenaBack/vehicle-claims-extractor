"""Score one extracted accident against its golden label, field by field.

Units: each scalar field is one unit; list fields score intersection over union;
each vehicle contributes five units (label, year, make, model, towed).
An empty list matching an empty list is one correct unit, like a matching null.
"""

from dataclasses import dataclass
from typing import Any

from ..schema import VehicleAccident
from .value_normalizer import normalize_value
from .vehicle_matcher import VEHICLE_FIELDS, match_vehicles

SCALAR_FIELDS = (
    "accident_type",
    "road_surface",
    "lighting",
    "location_type",
    "speed_limit_mph",
    "injuries_reported",
    "critical_reason",
)
LIST_FIELDS = ("weather", "area_type")


@dataclass(frozen=True)
class FieldMismatch:
    field: str      # e.g. "lighting", "weather", "vehicles.make"
    expected: Any   # None for an extra produced vehicle
    produced: Any   # None for a missed vehicle or a failed extraction


@dataclass(frozen=True)
class AccidentScore:
    correct: int
    total: int
    by_field: dict[str, tuple[int, int]]
    mismatches: tuple[FieldMismatch, ...]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total


def score_accident(expected: VehicleAccident, produced: VehicleAccident | None) -> AccidentScore:
    """Compare one prediction with one golden label. None means the extraction failed."""
    scorer = _Scorer()
    gold = expected.model_dump(mode="json")
    pred = produced.model_dump(mode="json") if produced is not None else None

    for field in SCALAR_FIELDS:
        scorer.scalar(field, gold[field], pred[field] if pred else None, failed=pred is None)

    for field in LIST_FIELDS:
        scorer.items(field, gold[field], pred[field] if pred else None)

    scorer.vehicles(gold["vehicles"], pred["vehicles"] if pred else None)
    return scorer.result()


class _Scorer:
    """Accumulates correct/total units and mismatches for one accident description."""

    def __init__(self) -> None:
        self._counts: dict[str, list[int]] = {}
        self._mismatches: list[FieldMismatch] = []

    def _add(self, field: str, correct: int, total: int) -> None:
        counts = self._counts.setdefault(field, [0, 0])
        counts[0] += correct
        counts[1] += total

    def scalar(self, field: str, expected: Any, produced: Any, *, failed: bool) -> None:
        correct = not failed and normalize_value(expected) == normalize_value(produced)
        self._add(field, int(correct), 1)
        if not correct:
            self._mismatches.append(FieldMismatch(field, expected, produced))

    def items(self, field: str, expected: list, produced: list | None) -> None:
        """Intersection over union; a failed extraction scores 0 over the expected items."""
        gold = {normalize_value(item) for item in expected}
        if produced is None:
            correct, total = 0, max(len(gold), 1)
        else:
            pred = {normalize_value(item) for item in produced}
            union = gold | pred
            correct, total = (len(gold & pred), len(union)) if union else (1, 1)
        self._add(field, correct, total)
        if correct < total:
            self._mismatches.append(FieldMismatch(
                field, sorted(expected), sorted(produced) if produced is not None else None,
            ))

    def vehicles(self, expected: list[dict], produced: list[dict] | None) -> None:
        if produced is None:
            if not expected:
                self._add("vehicles", 0, 1)
                self._mismatches.append(FieldMismatch("vehicles", [], None))
            _, missed, _ = match_vehicles(expected, [])
            for vehicle in missed:
                self._vehicle_pair(vehicle, None)
            return
        if not expected and not produced:
            self._add("vehicles", 1, 1)
            return

        pairs, missed, extra = match_vehicles(expected, produced)
        for gold, pred in pairs:
            self._vehicle_pair(gold, pred)
        for gold in missed:
            self._vehicle_pair(gold, None)
        for pred in extra:
            self._vehicle_pair(None, pred)

    def _vehicle_pair(self, expected: dict | None, produced: dict | None) -> None:
        """Five units; a missing side makes all five incorrect."""
        for field in VEHICLE_FIELDS:
            gold = expected[field] if expected else None
            pred = produced[field] if produced else None
            correct = expected is not None and produced is not None and normalize_value(gold) == normalize_value(pred)
            self._add(f"vehicles.{field}", int(correct), 1)
            if not correct:
                self._mismatches.append(FieldMismatch(f"vehicles.{field}", gold, pred))

    def result(self) -> AccidentScore:
        by_field = {field: (c, t) for field, (c, t) in self._counts.items()}
        return AccidentScore(
            correct=sum(c for c, _ in by_field.values()),
            total=sum(t for _, t in by_field.values()),
            by_field=by_field,
            mismatches=tuple(self._mismatches),
        )
