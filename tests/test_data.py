from backend.app.data import generate_demo_bars


def test_demo_bars_are_reproducible_and_valid() -> None:
    first = generate_demo_bars("600519", 40)
    second = generate_demo_bars("600519", 40)
    assert first == second
    assert len(first) == 40
    assert all(bar["low"] <= min(bar["open"], bar["close"]) for bar in first)
    assert all(bar["high"] >= max(bar["open"], bar["close"]) for bar in first)
    assert all(bar["volume"] > 0 for bar in first)

