import pandas as pd

from src.backtest import backtest_weights


def test_backtest_uses_previous_day_weights_and_charges_turnover_cost():
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    close = pd.DataFrame({"AAA": [100.0, 110.0, 121.0]}, index=dates)
    weights = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=dates)

    result = backtest_weights(close, weights)

    assert result.loc[dates[0], "turnover"] == 1.0
    assert round(result.loc[dates[0], "tc"], 4) == 0.001
    assert result.loc[dates[0], "port_ret_gross"] == 0.0
    assert round(result.loc[dates[1], "port_ret_gross"], 4) == 0.1


def test_backtest_accepts_custom_cost_bps():
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    close = pd.DataFrame({"AAA": [100.0, 101.0]}, index=dates)
    weights = pd.DataFrame({"AAA": [1.0, 1.0]}, index=dates)

    result = backtest_weights(close, weights, cost_bps=20)

    assert round(result.loc[dates[0], "tc"], 4) == 0.002
