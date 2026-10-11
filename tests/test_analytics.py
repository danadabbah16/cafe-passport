from datetime import date, timedelta

import pytest

from analytics import adjusted_score, rank_cafes, recency_weight, weighted_score

TODAY = date(2026, 10, 12)


def days_ago(n):
    return (TODAY - timedelta(days=n)).strftime("%Y-%m-%d")


def test_weight_today_is_one():
    assert recency_weight(days_ago(0), TODAY, half_life=60) == pytest.approx(1.0)

def test_weight_halves_at_half_life():
    assert recency_weight(days_ago(60), TODAY, half_life=60) == pytest.approx(0.5)

def test_weight_quarter_at_double_half_life():
    assert recency_weight(days_ago(120), TODAY, half_life=60) == pytest.approx(0.25)

def test_weighted_score_hand_math():
    # 9 from 120 days ago (weight 0.25) + 6 today (weight 1.0) -> 8.25/1.25 = 6.6
    visits = [
        {"visit_date": days_ago(120), "rating": 9},
        {"visit_date": days_ago(0), "rating": 6},
    ]
    assert weighted_score(visits, TODAY) == pytest.approx(6.6, abs=0.01)

def test_weighted_score_empty_is_zero():
    assert weighted_score([], TODAY) == 0.0

def test_adjustment_pulls_small_samples_to_mean():
    # 1 visit scoring 10, global mean 7, k=3 -> (10 + 21)/4 = 7.75
    assert adjusted_score(10, 1, 7.0, k=3) == pytest.approx(7.75)

def test_adjustment_barely_moves_large_samples():
    many = adjusted_score(9.0, 20, 7.0, k=3)
    few = adjusted_score(9.0, 1, 7.0, k=3)
    assert many > few
    assert many == pytest.approx(9.0, abs=0.3)

def test_one_lucky_visit_does_not_top_strong_regular():
    # A mediocre third cafe drags the global mean down, so the single 10
    # shrinks hard toward it while the 8-visit cafe barely moves.
    lucky = [{"visit_date": days_ago(1), "rating": 10}]
    regular = [{"visit_date": days_ago(i * 5), "rating": 9} for i in range(8)]
    mediocre = [{"visit_date": days_ago(i * 3), "rating": 5} for i in range(6)]
    ranked = rank_cafes({"Lucky": lucky, "Regular": regular, "Mediocre": mediocre}, TODAY)
    assert ranked[0]["cafe"] == "Regular"
    assert ranked[-1]["cafe"] == "Mediocre"

def test_rank_cafes_empty():
    assert rank_cafes({}, TODAY) == []