from coach_connect.exercises import EXERCISES
from coach_connect.plan import WORKOUTS
from coach_connect.progression import LoggedSet, SetTarget, suggest, suggest_free, warmup_sets

INCLINE = WORKOUTS["A"]["exercises"][0]
LATERAL = WORKOUTS["A"]["exercises"][1]
DB_BENCH = WORKOUTS["A"]["exercises"][2]
CHIN_UP = WORKOUTS["B"]["exercises"][0]


def logged(*pairs):
    return [LoggedSet(w, r) for w, r in pairs]


def loads(suggestion):
    return [(s.weight_kg, s.reps) for s in suggestion.sets]


def test_rpt_adds_load_when_every_rep_is_closed():
    # The plan's example: 60×5, 54×6, 48×8 all closed -> +1.25 kg, then −10% of the top set each step.
    result = suggest(INCLINE, EXERCISES["incline_barbell_bench"], logged((60, 5), (54, 6), (48, 8)),
                     ramp_up=False, bodyweight=70)

    assert result.progressed
    assert loads(result) == [(61.25, 5), (55.0, 6), (49.0, 8)]


def test_rpt_repeats_loads_when_a_set_falls_short():
    result = suggest(INCLINE, EXERCISES["incline_barbell_bench"], logged((60, 5), (54, 5), (48, 8)),
                     ramp_up=False, bodyweight=70)

    assert not result.progressed
    assert loads(result) == [(60, 5), (54.0, 6), (48.0, 8)]


def test_dumbbells_progress_by_two_kg_and_round_to_available_pairs():
    result = suggest(DB_BENCH, EXERCISES["dumbbell_bench_press"], logged((24, 6), (22, 8), (20, 10)),
                     ramp_up=False, bodyweight=70)

    assert loads(result) == [(26.0, 6), (24.0, 8), (20.0, 10)]


def test_weighted_chin_up_takes_ten_percent_of_bodyweight_plus_load():
    # The plan's example: 70 + 10 = 80 kg -> second set +2 kg -> third set bodyweight.
    result = suggest(CHIN_UP, EXERCISES["weighted_chin_up"], logged((10, 5), (2, 5), (0, 8)),
                     ramp_up=False, bodyweight=70)

    assert not result.progressed
    assert loads(result) == [(10, 5), (2.0, 6), (0.0, 8)]
    assert result.sets[2].note == "corpo libero"


def test_bodyweight_chin_ups_move_to_added_load_after_three_sets_of_ten():
    exercise = EXERCISES["weighted_chin_up"]

    building = suggest(CHIN_UP, exercise, logged((0, 8), (0, 7), (0, 6)), ramp_up=False, bodyweight=70)
    ready = suggest(CHIN_UP, exercise, logged((0, 10), (0, 10), (0, 10)), ramp_up=False, bodyweight=70)

    assert [s.reps for s in building.sets] == [9, 8, 7]
    assert ready.progressed and ready.sets[0].weight_kg == 2.5


def test_ramp_up_weeks_keep_the_same_load_on_every_set():
    result = suggest(INCLINE, EXERCISES["incline_barbell_bench"], logged((55, 6), (55, 6), (55, 5)),
                     ramp_up=True, bodyweight=70)

    assert loads(result) == [(55, 6), (55, 6), (55, 5)]


def test_first_time_leaves_the_load_to_choose():
    result = suggest(INCLINE, EXERCISES["incline_barbell_bench"], [], ramp_up=False, bodyweight=70)

    assert loads(result) == [(None, 5), (None, 6), (None, 8)]


def test_accessories_go_up_only_after_the_top_of_the_range_on_every_set():
    exercise = EXERCISES["lateral_raise"]

    up = suggest(LATERAL, exercise, logged((8, 12), (8, 12), (8, 12)), ramp_up=False, bodyweight=70)
    same = suggest(LATERAL, exercise, logged((8, 12), (8, 11), (8, 10)), ramp_up=False, bodyweight=70)

    assert up.progressed and loads(up) == [(10.0, 8)] * 3
    assert not same.progressed and loads(same) == [(8, 12), (8, 11), (8, 10)]


def test_warmup_is_fifty_seventy_five_ninety_percent_of_the_first_set():
    assert warmup_sets(EXERCISES["incline_barbell_bench"], 60) == [
        SetTarget(30.0, 5),
        SetTarget(45.0, 3),
        SetTarget(55.0, 1),
    ]
    assert warmup_sets(EXERCISES["weighted_chin_up"], 10) == []


def test_exercises_outside_the_plan_repeat_last_session():
    assert loads(suggest_free(logged((40, 10), (40, 9)))) == [(40, 10), (40, 9)]
