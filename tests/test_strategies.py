from backend.app.data import generate_demo_bars
from backend.app.strategies import STRATEGIES, evaluate_strategy, score_latest


def test_every_strategy_returns_aligned_series() -> None:
    bars = generate_demo_bars("300750", 360)
    for strategy in STRATEGIES:
        result = evaluate_strategy(bars, strategy)
        assert len(result.positions) == len(bars)
        assert set(result.positions).issubset({0, 1})
        assert all(len(series) == len(bars) for series in result.indicators.values())


def test_latest_score_stays_in_public_range() -> None:
    bars = generate_demo_bars("600036", 360)
    result = evaluate_strategy(bars, "trend")
    score = score_latest(bars, result)
    assert 0 <= score["score"] <= 100
    assert score["rating"] in {"强势", "关注", "中性", "弱势"}

