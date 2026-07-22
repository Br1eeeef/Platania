from backend.app.indicators import atr, rsi, sma


def test_sma_keeps_warmup_values_empty() -> None:
    assert sma([1, 2, 3, 4], 3) == [None, None, 2.0, 3.0]


def test_rsi_reports_full_strength_for_only_gains() -> None:
    values = list(range(1, 30))
    values_rsi = rsi(values, 14)
    assert values_rsi[13] is None
    assert values_rsi[-1] == 100.0


def test_atr_uses_gaps_from_previous_close() -> None:
    result = atr([10, 14, 13], [9, 12, 11], [9.5, 13, 12], window=2)
    assert result[0] is None
    assert result[1] == 2.75

