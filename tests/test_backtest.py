from backend.app.backtest import TradingCosts, run_backtest


def test_signal_executes_at_next_open_and_respects_lot_size() -> None:
    bars = [
        {"date": "2026-01-01", "open": 10, "close": 10},
        {"date": "2026-01-02", "open": 10, "close": 11},
        {"date": "2026-01-05", "open": 12, "close": 12},
        {"date": "2026-01-06", "open": 12, "close": 12},
    ]
    positions = [1, 0, 0, 0]
    costs = TradingCosts(commission_rate=0, minimum_commission=0, stamp_duty_rate=0, slippage_rate=0)
    result = run_backtest(bars, positions, initial_cash=10_050, costs=costs)
    assert result["trade_count"] == 1
    assert result["trades"][0]["entry_date"] == "2026-01-02"
    assert result["trades"][0]["exit_date"] == "2026-01-05"
    assert result["trades"][0]["quantity"] == 1000
    assert result["final_equity"] == 12_050

