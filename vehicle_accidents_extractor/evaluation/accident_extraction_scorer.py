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
    golden_value: Any    # None for an extra extracted vehicle
    extracted_value: Any # None for a missed vehicle or failed extraction


@dataclass(frozen=True)
class AccidentScore:
    correct: int
    total: int
    by_field: dict[str, tuple[int, int]]
    mismatches: tuple[FieldMismatch, ...]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total


def score_accident(
    golden_label: VehicleAccident,
    extracted_accident: VehicleAccident | None,
) -> AccidentScore:
    """Compare an extracted accident with its golden label; None means extraction failed."""
    scorer = _Scorer()
    golden_fields = golden_label.model_dump(mode="json")
    extracted_fields = extracted_accident.model_dump(mode="json") if extracted_accident is not None else None

    for field in SCALAR_FIELDS:
        scorer.scalar(
            field,
            golden_fields[field],
            extracted_fields[field] if extracted_fields else None,
            extraction_failed=extracted_fields is None,
        )

    for field in LIST_FIELDS:
        scorer.items(field, golden_fields[field], extracted_fields[field] if extracted_fields else None)

    scorer.vehicles(
        golden_fields["vehicles"],
        extracted_fields["vehicles"] if extracted_fields else None,
    )
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

    def scalar(
        self,
        field: str,
        golden_value: Any,
        extracted_value: Any,
        *,
        extraction_failed: bool,
    ) -> None:
        correct = not extraction_failed and normalize_value(golden_value) == normalize_value(extracted_value)
        self._add(field, int(correct), 1)
        if not correct:
            self._mismatches.append(FieldMismatch(field, golden_value, extracted_value))

    def items(self, field: str, golden_items: list, extracted_items: list | None) -> None:
        """Intersection over union; a failed extraction scores 0 over the golden items."""
        normalized_golden_items = {normalize_value(item) for item in golden_items}
        if extracted_items is None:
            correct, total = 0, max(len(normalized_golden_items), 1)
        else:
            normalized_extracted_items = {normalize_value(item) for item in extracted_items}
            union = normalized_golden_items | normalized_extracted_items
            correct, total = (
                (len(normalized_golden_items & normalized_extracted_items), len(union))
                if union else (1, 1)
            )
        self._add(field, correct, total)
        if correct < total:
            self._mismatches.append(FieldMismatch(
                field,
                sorted(golden_items),
                sorted(extracted_items) if extracted_items is not None else None,
            ))

    def vehicles(self, golden_vehicles: list[dict], extracted_vehicles: list[dict] | None) -> None:
        if extracted_vehicles is None:
            if not golden_vehicles:
                self._add("vehicles", 0, 1)
                self._mismatches.append(FieldMismatch("vehicles", [], None))
            _, missed_golden_vehicles, _ = match_vehicles(golden_vehicles, [])
            for golden_vehicle in missed_golden_vehicles:
                self._vehicle_pair(golden_vehicle, None)
            return
        if not golden_vehicles and not extracted_vehicles:
            self._add("vehicles", 1, 1)
            return

        pairs, missed_golden_vehicles, extra_extracted_vehicles = match_vehicles(
            golden_vehicles, extracted_vehicles,
        )
        for golden_vehicle, extracted_vehicle in pairs:
            self._vehicle_pair(golden_vehicle, extracted_vehicle)
        for golden_vehicle in missed_golden_vehicles:
            self._vehicle_pair(golden_vehicle, None)
        for extracted_vehicle in extra_extracted_vehicles:
            self._vehicle_pair(None, extracted_vehicle)

    def _vehicle_pair(
        self,
        golden_vehicle: dict | None,
        extracted_vehicle: dict | None,
    ) -> None:
        """Five units; a missing side makes all five incorrect."""
        for field in VEHICLE_FIELDS:
            golden_value = golden_vehicle[field] if golden_vehicle else None
            extracted_value = extracted_vehicle[field] if extracted_vehicle else None
            correct = (
                golden_vehicle is not None
                and extracted_vehicle is not None
                and normalize_value(golden_value) == normalize_value(extracted_value)
            )
            self._add(f"vehicles.{field}", int(correct), 1)
            if not correct:
                self._mismatches.append(FieldMismatch(f"vehicles.{field}", golden_value, extracted_value))

    def result(self) -> AccidentScore:
        by_field = {field: (c, t) for field, (c, t) in self._counts.items()}
        return AccidentScore(
            correct=sum(c for c, _ in by_field.values()),
            total=sum(t for _, t in by_field.values()),
            by_field=by_field,
            mismatches=tuple(self._mismatches),
        )
