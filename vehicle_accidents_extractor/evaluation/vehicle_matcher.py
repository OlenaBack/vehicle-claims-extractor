"""Pair vehicles by label, then maximum normalized field agreement."""

from itertools import permutations

from .value_normalizer import normalize_value

VEHICLE_FIELDS = ("label", "year", "make", "model", "towed")


def vehicle_agreement(expected: dict, produced: dict) -> int:
    """Number of the five vehicle fields that match."""
    return sum(normalize_value(expected[f]) == normalize_value(produced[f]) for f in VEHICLE_FIELDS)


def match_vehicles(
    expected: list[dict], produced: list[dict],
) -> tuple[list[tuple[dict, dict]], list[dict], list[dict]]:
    """Pair vehicles independently of list order.

    1. Equal non-null labels are paired.
    2. Remaining vehicles are paired to maximize field agreement, each used once.
    3. Ties are broken by vehicle contents, and every returned list is sorted by contents.
    Returns (pairs, missed expected vehicles, extra produced vehicles).
    """
    produced_by_label = {normalize_value(v["label"]): v for v in produced if v["label"] is not None}
    pairs: list[tuple[dict, dict]] = []
    gold_left: list[dict] = []
    for vehicle in expected:
        partner = produced_by_label.pop(normalize_value(vehicle["label"]), None) if vehicle["label"] is not None else None
        if partner is not None:
            pairs.append((vehicle, partner))
        else:
            gold_left.append(vehicle)
    paired_ids = {id(pred) for _, pred in pairs}
    pred_left = [v for v in produced if id(v) not in paired_ids]

    best = _best_assignment(gold_left, pred_left)
    pairs += best
    matched_gold = {id(g) for g, _ in best}
    matched_pred = {id(p) for _, p in best}
    missed = [g for g in gold_left if id(g) not in matched_gold]
    extra = [p for p in pred_left if id(p) not in matched_pred]
    return (
        sorted(pairs, key=lambda pair: (_vehicle_key(pair[0]), _vehicle_key(pair[1]))),
        sorted(missed, key=_vehicle_key),
        sorted(extra, key=_vehicle_key),
    )


def _best_assignment(gold: list[dict], pred: list[dict]) -> list[tuple[dict, dict]]:
    """Brute-force the pairing with the most matching fields (vehicle counts are small).

    Ties are broken by the vehicles' contents, not their list positions, so the
    per-field scores and mismatches are the same however the lists are ordered.
    """
    if not gold or not pred:
        return []
    if len(gold) <= len(pred):
        candidates = (list(zip(gold, chosen)) for chosen in permutations(pred, len(gold)))
    else:
        candidates = (list(zip(chosen, pred)) for chosen in permutations(gold, len(pred)))
    return min(candidates, key=lambda pairs: (-sum(vehicle_agreement(g, p) for g, p in pairs), _signature(pairs)))


def _signature(pairs: list[tuple[dict, dict]]) -> tuple:
    """Order-independent description of a pairing, used only to break ties."""
    return tuple(sorted((_vehicle_key(g), _vehicle_key(p)) for g, p in pairs))


def _vehicle_key(vehicle: dict) -> tuple:
    return tuple(repr(normalize_value(vehicle[field])) for field in VEHICLE_FIELDS)
