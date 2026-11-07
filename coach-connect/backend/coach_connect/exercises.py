"""Exercise catalog used by the workout log and the plan."""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Load added after closing every rep: 1-1.25 kg on barbells, 2 kg on dumbbells (from the plan).
INCREMENT_KG = {
    "barbell": 1.25,
    "dumbbell": 2.0,
    "cable": 2.5,
    "machine": 2.5,
    "weighted_bodyweight": 1.25,
    "bodyweight": 0.0,
}
# Rounding applied to computed back-off sets (dumbbells usually come in 2 kg steps).
ROUNDING_KG = {
    "barbell": 0.5,
    "dumbbell": 2.0,
    "cable": 2.5,
    "machine": 2.5,
    "weighted_bodyweight": 0.5,
    "bodyweight": 0.0,
}


@dataclass(frozen=True)
class Exercise:
    id: str
    name: str
    group: str
    equipment: str
    measure: str = "reps"  # "reps" or "seconds"

    @property
    def increment_kg(self) -> float:
        return INCREMENT_KG[self.equipment]

    @property
    def rounding_kg(self) -> float:
        return ROUNDING_KG[self.equipment]

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


_CATALOG = (
    # Workout A · Push
    Exercise("incline_barbell_bench", "Panca inclinata bilanciere", "Petto", "barbell"),
    Exercise("lateral_raise", "Alzate laterali", "Spalle", "dumbbell"),
    Exercise("dumbbell_bench_press", "Panca piana manubri", "Petto", "dumbbell"),
    Exercise("cable_pushdown", "Push down ai cavi", "Tricipiti", "cable"),
    # Workout B · Pull
    Exercise("weighted_chin_up", "Chin-up zavorrate (presa supina)", "Schiena", "weighted_bodyweight"),
    Exercise("dumbbell_row", "Rematore con manubrio", "Schiena", "dumbbell"),
    Exercise("seated_rear_delt_raise", "Alzate posteriori da seduto", "Spalle", "dumbbell"),
    Exercise("barbell_curl", "Curl bilanciere", "Bicipiti", "barbell"),
    # Abs circuit at the end of every workout
    Exercise("jackknife_crunch", "Crunch a libro", "Addome", "bodyweight"),
    Exercise("lying_leg_raise", "Leg raise da sdraiato", "Addome", "bodyweight"),
    Exercise("russian_twist", "Russian twist", "Addome", "bodyweight"),
    Exercise("plank", "Plank", "Addome", "bodyweight", measure="seconds"),
    # Variants from week 13
    Exercise("military_press", "Military press", "Spalle", "barbell"),
    Exercise("weighted_pull_up", "Pull-up zavorrate", "Schiena", "weighted_bodyweight"),
    Exercise("incline_dumbbell_curl", "Curl su panca inclinata", "Bicipiti", "dumbbell"),
    Exercise("cable_french_press", "French press al cavo", "Tricipiti", "cable"),
    # Other common exercises
    Exercise("bench_press", "Panca piana bilanciere", "Petto", "barbell"),
    Exercise("dips", "Dip alle parallele", "Petto", "weighted_bodyweight"),
    Exercise("push_up", "Piegamenti", "Petto", "bodyweight"),
    Exercise("cable_fly", "Croci ai cavi", "Petto", "cable"),
    Exercise("dumbbell_shoulder_press", "Lento manubri", "Spalle", "dumbbell"),
    Exercise("face_pull", "Face pull", "Spalle", "cable"),
    Exercise("overhead_triceps_extension", "French press manubrio", "Tricipiti", "dumbbell"),
    Exercise("lat_pulldown", "Lat machine", "Schiena", "machine"),
    Exercise("seated_cable_row", "Pulley basso", "Schiena", "cable"),
    Exercise("barbell_row", "Rematore bilanciere", "Schiena", "barbell"),
    Exercise("hammer_curl", "Curl a martello", "Bicipiti", "dumbbell"),
    Exercise("back_squat", "Squat bilanciere", "Gambe", "barbell"),
    Exercise("deadlift", "Stacco da terra", "Gambe", "barbell"),
    Exercise("romanian_deadlift", "Stacco rumeno", "Gambe", "barbell"),
    Exercise("leg_press", "Leg press", "Gambe", "machine"),
    Exercise("walking_lunge", "Affondi camminati", "Gambe", "dumbbell"),
    Exercise("leg_curl", "Leg curl", "Gambe", "machine"),
    Exercise("leg_extension", "Leg extension", "Gambe", "machine"),
    Exercise("calf_raise", "Calf raise", "Gambe", "machine"),
    Exercise("hanging_leg_raise", "Leg raise alla sbarra", "Addome", "bodyweight"),
)

EXERCISES: dict[str, Exercise] = {exercise.id: exercise for exercise in _CATALOG}
GROUPS = ("Petto", "Spalle", "Tricipiti", "Schiena", "Bicipiti", "Gambe", "Addome")


def get_exercise(exercise_id: str) -> Exercise | None:
    return EXERCISES.get(exercise_id)
