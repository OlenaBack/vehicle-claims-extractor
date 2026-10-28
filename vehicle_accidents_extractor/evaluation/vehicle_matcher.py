"""Pair vehicles by label, then maximum normalized field agreement."""

from itertools import permutations

from .value_normalizer import normalize_value

VEHICLE_FIELDS = ("label", "year", "make", "model", "towed")


def vehicle_agreement(golden_vehicle: dict, extracted_vehicle: dict) -> int:
    """Number of the five vehicle fields that match."""
    return sum(
        normalize_value(golden_vehicle[field]) == normalize_value(extracted_vehicle[field])
        for field in VEHICLE_FIELDS
    )


def match_vehicles(
    golden_vehicles: list[dict], extracted_vehicles: list[dict],
) -> tuple[list[tuple[dict, dict]], list[dict], list[dict]]:
    """Pair vehicles independently of list order.

    1. Equal non-null labels pair golden and extracted vehicles.
    2. Remaining vehicles are paired to maximize field agreement, each used once.
    3. Ties are broken by vehicle contents, and every returned list is sorted by contents.
    Returns (pairs, missed golden vehicles, extra extracted vehicles).
    """
    extracted_by_label = {
        normalize_value(vehicle["label"]): vehicle
        for vehicle in extracted_vehicles
        if vehicle["label"] is not None
    }
    pairs: list[tuple[dict, dict]] = []
    golden_vehicles_left: list[dict] = []
    for golden_vehicle in golden_vehicles:
        matching_extracted_vehicle = (
            extracted_by_label.pop(normalize_value(golden_vehicle["label"]), None)
            if golden_vehicle["label"] is not None
            else None
        )
        if matching_extracted_vehicle is not None:
            pairs.append((golden_vehicle, matching_extracted_vehicle))
        else:
            golden_vehicles_left.append(golden_vehicle)
    paired_extracted_vehicle_ids = {id(extracted_vehicle) for _, extracted_vehicle in pairs}
    extracted_vehicles_left = [
        vehicle for vehicle in extracted_vehicles
        if id(vehicle) not in paired_extracted_vehicle_ids
    ]

    best_pairs = _best_assignment(golden_vehicles_left, extracted_vehicles_left)
    pairs += best_pairs
    matched_golden_vehicle_ids = {id(vehicle) for vehicle, _ in best_pairs}
    matched_extracted_vehicle_ids = {id(vehicle) for _, vehicle in best_pairs}
    missed_golden_vehicles = [
        vehicle for vehicle in golden_vehicles_left
        if id(vehicle) not in matched_golden_vehicle_ids
    ]
    extra_extracted_vehicles = [
        vehicle for vehicle in extracted_vehicles_left
        if id(vehicle) not in matched_extracted_vehicle_ids
    ]
    return (
        sorted(pairs, key=lambda pair: (_vehicle_key(pair[0]), _vehicle_key(pair[1]))),
        sorted(missed_golden_vehicles, key=_vehicle_key),
        sorted(extra_extracted_vehicles, key=_vehicle_key),
    )


def _best_assignment(
    golden_vehicles: list[dict],
    extracted_vehicles: list[dict],
) -> list[tuple[dict, dict]]:
    """Brute-force the pairing with the most matching fields (vehicle counts are small).

    Ties are broken by the vehicles' contents, not their list positions, so the
    per-field scores and mismatches are the same however the lists are ordered.
    """
    if not golden_vehicles or not extracted_vehicles:
        return []
    if len(golden_vehicles) <= len(extracted_vehicles):
        candidates = (
            list(zip(golden_vehicles, chosen))
            for chosen in permutations(extracted_vehicles, len(golden_vehicles))
        )
    else:
        candidates = (
            list(zip(chosen, extracted_vehicles))
            for chosen in permutations(golden_vehicles, len(extracted_vehicles))
        )
    return min(
        candidates,
        key=lambda vehicle_pairs: (
            -sum(
                vehicle_agreement(golden_vehicle, extracted_vehicle)
                for golden_vehicle, extracted_vehicle in vehicle_pairs
            ),
            _signature(vehicle_pairs),
        ),
    )


def _signature(vehicle_pairs: list[tuple[dict, dict]]) -> tuple:
    """Order-independent description of a pairing, used only to break ties."""
    return tuple(
        sorted(
            (_vehicle_key(golden_vehicle), _vehicle_key(extracted_vehicle))
            for golden_vehicle, extracted_vehicle in vehicle_pairs
        )
    )


def _vehicle_key(accident_vehicle: dict) -> tuple:
    return tuple(repr(normalize_value(accident_vehicle[field])) for field in VEHICLE_FIELDS)
