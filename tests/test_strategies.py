import pandas as pd

from src.strategies import _mom_score, weights_momentum_rotation
from src.strategies import weights_sma_crossover


def test_momentum_score_uses_lookback_to_skip_window():
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame(
        {
            "A": [100.0, 110.0, 121.0, 133.1, 146.41],
            "B": [100.0, 100.0, 100.0, 100.0, 100.0],
        },
        index=dates,
    )

    score = _mom_score(prices, lookback=3, skip=1)

    assert round(score.loc[dates[3], "A"], 4) == 0.21
    assert score.loc[dates[3], "B"] == 0.0


def test_momentum_rotation_allocates_to_top_assets_after_signal_exists():
    dates = pd.date_range("2023-01-31", periods=15, freq="ME")
    prices = pd.DataFrame(
        {
            "A": [100.0 * (1.03**i) for i in range(15)],
            "B": [100.0 for _ in range(15)],
        },
        index=dates,
    )

    weights = weights_momentum_rotation(prices, top_n=1)

    assert weights.loc[dates[12], "A"] == 1.0
    assert weights.loc[dates[12], "B"] == 0.0


def test_momentum_rotation_returns_zero_weights_when_history_is_too_short():
    dates = pd.date_range("2024-01-31", periods=5, freq="ME")
    prices = pd.DataFrame({"A": [1, 2, 3, 4, 5]}, index=dates)

    weights = weights_momentum_rotation(prices, top_n=1)

    assert list(weights.columns) == ["A"]
    assert weights.sum().iloc[0] == 0.0


def test_sma_crossover_accepts_custom_windows():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    close = pd.Series([1.0, 1.0, 2.0, 3.0, 4.0], index=dates, name="AAA")

    weights = weights_sma_crossover(close, short_window=2, long_window=3)

    assert weights.loc[dates[-1], "AAA"] == 1.0
