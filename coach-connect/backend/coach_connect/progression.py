"""Load suggestions derived from the plan's progression rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .exercises import Exercise


@dataclass(frozen=True)
class LoggedSet:
    weight_kg: float | None
    reps: int | None
    seconds: int | None = None


@dataclass(frozen=True)
class SetTarget:
    weight_kg: float | None
    reps: int | None
    note: str | None = None


@dataclass(frozen=True)
class Suggestion:
    sets: list[SetTarget]
    message: str
    progressed: bool = False
    warmup: list[SetTarget] = field(default_factory=list)


def round_to(value: float, step: float) -> float:
    return round(round(value / step) * step, 2) if step else round(value, 2)


def _fmt(kg: float) -> str:
    return f"{kg:g}".replace(".", ",")


def _closed(last: list[LoggedSet], targets: list[int]) -> bool:
    return len(last) >= len(targets) and all((s.reps or 0) >= t for s, t in zip(last, targets))


def _rpt_sets(exercise: Exercise, top: float, reps: list[int], bodyweight: float | None) -> list[SetTarget]:
    if exercise.equipment == "weighted_bodyweight" and bodyweight:
        # The 10% is taken on bodyweight + added load (70 + 10 = 80 kg -> +2 kg -> bodyweight).
        total = bodyweight + top
        targets = []
        for i, r in enumerate(reps):
            added = top if i == 0 else max(0.0, round_to(total * (1 - 0.1 * i) - bodyweight, exercise.rounding_kg))
            targets.append(SetTarget(added, r, "corpo libero" if added == 0 else None))
        return targets
    return [
        SetTarget(top if i == 0 else round_to(top * (1 - 0.1 * i), exercise.rounding_kg), r)
        for i, r in enumerate(reps)
    ]


def suggest(
    item: dict[str, Any],
    exercise: Exercise,
    last: list[LoggedSet],
    *,
    ramp_up: bool,
    bodyweight: float | None,
) -> Suggestion:
    """Next-session targets for a plan exercise, given the sets logged last time."""
    if item["scheme"] == "rpt":
        return _suggest_rpt(item["reps"], exercise, last, ramp_up=ramp_up, bodyweight=bodyweight)
    return _suggest_straight(item["sets"], item["rep_range"], exercise, last)


def _suggest_rpt(
    reps: list[int], exercise: Exercise, last: list[LoggedSet], *, ramp_up: bool, bodyweight: float | None
) -> Suggestion:
    top = last[0].weight_kg if last else None
    if exercise.equipment == "weighted_bodyweight" and last and not top:
        if _closed(last, [10] * len(reps)):
            return Suggestion(_rpt_sets(exercise, 2.5, reps, bodyweight), "Sei arrivato a 3 × 10: inizia con 2,5 kg di zavorra.", True)
        return Suggestion(
            [SetTarget(0.0, min((s.reps or 0) + 1, 10), "corpo libero") for s in last[: len(reps)]],
            "A corpo libero: aggiungi ripetizioni fino a 3 × 10, poi passa a 2,5-5 kg di zavorra.",
        )
    if top is None:
        return Suggestion(
            [SetTarget(None, r) for r in reps],
            "Prima volta: scegli il carico della prima serie, le altre a −10% con più ripetizioni.",
        )
    if ramp_up:
        return Suggestion(
            [SetTarget(top, last[i].reps if i < len(last) else reps[0]) for i in range(len(reps))],
            "Fase di ripresa: 3 serie con lo stesso carico, 2-3 ripetizioni dal cedimento.",
        )
    if _closed(last, reps):
        top = round(top + exercise.increment_kg, 2)
        return Suggestion(
            _rpt_sets(exercise, top, reps, bodyweight),
            f"Hai chiuso tutte le ripetizioni: +{_fmt(exercise.increment_kg)} kg sulla prima serie.",
            True,
        )
    return Suggestion(
        _rpt_sets(exercise, top, reps, bodyweight),
        "Stessi carichi dell'ultima volta: prova a chiudere tutte le ripetizioni.",
    )


def _suggest_straight(sets: int, rep_range: list[int], exercise: Exercise, last: list[LoggedSet]) -> Suggestion:
    low, high = rep_range
    weights = [s.weight_kg for s in last if s.weight_kg is not None]
    if not last or (not weights and exercise.equipment != "bodyweight"):
        return Suggestion([SetTarget(None, None) for _ in range(sets)], f"Scegli un carico che ti permetta {low}-{high} ripetizioni pulite.")
    weight = max(weights) if weights else None
    if weight is not None and exercise.increment_kg and _closed(last, [high] * sets):
        weight = round(weight + exercise.increment_kg, 2)
        return Suggestion(
            [SetTarget(weight, low) for _ in range(sets)],
            f"Massimo delle ripetizioni in tutte le serie: +{_fmt(exercise.increment_kg)} kg.",
            True,
        )
    return Suggestion(
        [SetTarget(weight, last[i].reps if i < len(last) else low) for i in range(sets)],
        f"Stesso peso finché non arrivi a {high} ripetizioni in tutte le serie.",
    )


def suggest_free(last: list[LoggedSet]) -> Suggestion:
    """Exercises outside the plan simply repeat the previous session."""
    if not last:
        return Suggestion([SetTarget(None, None)], "Nuovo esercizio.")
    return Suggestion([SetTarget(s.weight_kg, s.reps) for s in last], "Come l'ultima volta.")


def warmup_sets(exercise: Exercise, first_set_kg: float | None) -> list[SetTarget]:
    """50% × 5, 75% × 3, 90% × 1 of the first working set, before the first exercise only."""
    if not first_set_kg or exercise.equipment not in {"barbell", "dumbbell"}:
        return []
    step = 2.0 if exercise.equipment == "dumbbell" else 2.5
    return [SetTarget(round_to(first_set_kg * pct, step), reps) for pct, reps in ((0.5, 5), (0.75, 3), (0.9, 1))]
