"""The training plan ("Scheda Hybrid Athlete") as data, plus the calendar logic around it."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .exercises import EXERCISES

GYM = ("A", "B")
WEEKDAYS = ("Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica")

# Two-week rotation, Monday first: gym every other day with A and B alternating, two runs.
ROTATION = (
    ("A", "run_quality", "B", "rest", "A", "rest", "run_long"),
    ("B", "run_quality", "A", "rest", "B", "rest", "run_long"),
)

SESSIONS = {
    "A": {"title": "Workout A · Push", "short": "A", "kind": "gym"},
    "B": {"title": "Workout B · Pull", "short": "B", "kind": "gym"},
    "run_quality": {"title": "Corsa · Qualità", "short": "Q", "kind": "run", "description": "Ripetute, tempo o fartlek"},
    "run_long": {"title": "Corsa · Lungo", "short": "L", "kind": "run", "description": "Ritmo facile e costante"},
    "rest": {"title": "Riposo", "short": "–", "kind": "rest"},
}


def _rpt(exercise_id: str, reps: list[int], cue: str) -> dict[str, Any]:
    return {"exercise_id": exercise_id, "scheme": "rpt", "reps": reps, "sets": len(reps), "rep_range": None,
            "rest_s": 180, "main": True, "cue": cue}


def _straight(exercise_id: str, sets: int, rep_range: list[int], cue: str) -> dict[str, Any]:
    return {"exercise_id": exercise_id, "scheme": "straight", "reps": None, "sets": sets, "rep_range": rep_range,
            "rest_s": 120, "main": False, "cue": cue}


WORKOUTS: dict[str, dict[str, Any]] = {
    "A": {
        "title": "Workout A · Push",
        "focus": "Petto · Spalle · Tricipiti",
        "exercises": [
            _rpt("incline_barbell_bench", [5, 6, 8],
                 "Panca a 30-45°, scapole addotte e piedi piantati. Il bilanciere scende sulla parte alta del petto, "
                 "gomiti a circa 45°. Prima fai le serie di riscaldamento."),
            _straight("lateral_raise", 3, [8, 12],
                      "Gomiti leggermente flessi, sali fino all'altezza delle spalle guidando con i gomiti. "
                      "Niente slancio: se dondoli, il peso è troppo alto."),
            _rpt("dumbbell_bench_press", [6, 8, 10],
                 "Scapole strette, manubri ai lati del petto con i gomiti a 45°, poi spingi avvicinandoli in alto."),
            _straight("cable_pushdown", 3, [8, 12],
                      "Gomiti incollati ai fianchi, estendi completamente e contrai 1 secondo in basso."),
        ],
    },
    "B": {
        "title": "Workout B · Pull",
        "focus": "Schiena · Bicipiti",
        "exercises": [
            _rpt("weighted_chin_up", [5, 6, 8],
                 "Presa supina alla larghezza delle spalle, petto verso la sbarra, discesa completa. "
                 "Il 10% si calcola su peso corporeo + zavorra."),
            _straight("dumbbell_row", 3, [6, 10],
                      "Mano e ginocchio sulla panca, schiena piatta. Tira il gomito verso l'anca e tieni 1 secondo in alto."),
            _straight("seated_rear_delt_raise", 3, [10, 15],
                      "Busto appoggiato sulle cosce, apri le braccia con i gomiti morbidi. Carichi leggeri, movimento pulito."),
            _straight("barbell_curl", 3, [6, 10],
                      "Gomiti fermi ai fianchi, niente slancio con la schiena. Discesa controllata in 2-3 secondi."),
        ],
    },
}

ABS_CIRCUIT = {
    "rounds": "2-3 giri",
    "rest": "Nessuna pausa tra gli esercizi, 1' tra i giri",
    "exercises": [
        {"exercise_id": "jackknife_crunch", "target": "a cedimento", "cue": "Segnati le ripetizioni e prova a batterle."},
        {"exercise_id": "lying_leg_raise", "target": "12-15", "cue": "Scendi in 3 secondi, zona lombare sempre a terra."},
        {"exercise_id": "russian_twist", "target": "12-15 per lato", "cue": "Quando è facile, prendi un disco."},
        {"exercise_id": "plank", "target": "45-60\"", "cue": "Glutei stretti, gomiti spinti verso i piedi: più duro, non più lungo."},
    ],
}

RULES = [
    {"title": "RPT · Reverse Pyramid", "text": "Sui principali la serie più pesante è la prima, poi togli il 10% e aggiungi ripetizioni. Recupero 3'."},
    {"title": "Riscaldamento", "text": "Solo prima del primo esercizio: 50% × 5, 75% × 3, 90% × 1 del carico della serie 1, 2' tra le serie."},
    {"title": "Progressione principali", "text": "Quando chiudi tutte le ripetizioni sulle tre serie, la volta dopo aggiungi 1-1,25 kg (2 kg sui manubri)."},
    {"title": "Progressione complementari", "text": "Stesso peso finché fai il massimo delle ripetizioni in tutte le serie, poi aumenti il carico."},
    {"title": "Tecnica prima del carico", "text": "Se per chiudere le ripetizioni serve lo slancio, il peso è troppo alto."},
    {"title": "Se sei stanco", "text": "Accorcia i complementari, non i principali. La panca inclinata va sempre per prima, a mente fresca."},
]

PHASES = [
    {"from_week": 1, "to_week": 3, "name": "Ripresa",
     "text": "3 serie con lo stesso carico, 2-3 ripetizioni dal cedimento. Niente RPT: tendini e spalle si riabituano."},
    {"from_week": 4, "to_week": 12, "name": "RPT pieno",
     "text": "Schema RPT sui principali e progressione costante. Qui si costruisce la forza."},
    {"from_week": 13, "to_week": None, "name": "Variante",
     "text": "Military press al posto della panca manubri, pull-up al posto dei chin-up, curl su panca inclinata, French press al cavo."},
]

# Substitutions applied from week 13.
VARIANTS = {
    "dumbbell_bench_press": "military_press",
    "weighted_chin_up": "weighted_pull_up",
    "barbell_curl": "incline_dumbbell_curl",
    "cable_pushdown": "cable_french_press",
}

NUTRITION = [
    "Circa 140 g di proteine al giorno (2 g per kg), distribuite su 3-4 pasti.",
    "Più carboidrati nei giorni di corsa: se il peso scende, stai mangiando troppo poco per crescere.",
    "Una volta a settimana, a digiuno, peso e circonferenza vita: peso su e vita stabile vuol dire muscolo.",
]


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def week_number(start: date, day: date) -> int:
    """1-based program week of `day`, counting from the Monday of the start week."""
    return max(1, (monday_of(day) - monday_of(start)).days // 7 + 1)


def rotation_session(start: date, day: date) -> str:
    return ROTATION[(week_number(start, day) - 1) % 2][day.weekday()]


def phase_for(week: int) -> dict[str, Any]:
    for phase in PHASES:
        if week >= phase["from_week"] and (phase["to_week"] is None or week <= phase["to_week"]):
            return phase
    return PHASES[0]


def is_ramp_up(week: int) -> bool:
    return phase_for(week)["name"] == "Ripresa"


def workout_exercises(which: str, week: int) -> list[dict[str, Any]]:
    """Exercises of workout A or B for a program week, with the week-13 variants applied."""
    variant = week >= PHASES[-1]["from_week"]
    exercises = []
    for item in WORKOUTS[which]["exercises"]:
        exercise_id = VARIANTS.get(item["exercise_id"], item["exercise_id"]) if variant else item["exercise_id"]
        exercises.append({**item, "exercise_id": exercise_id, "name": EXERCISES[exercise_id].name})
    return exercises


def scheme_label(item: dict[str, Any]) -> str:
    if item["scheme"] == "rpt":
        return "RPT " + "/".join(str(r) for r in item["reps"])
    low, high = item["rep_range"]
    return f"{item['sets']} × {low}-{high}"
