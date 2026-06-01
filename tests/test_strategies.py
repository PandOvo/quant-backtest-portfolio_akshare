import pandas as pd

from src.strategies import _mom_score, weights_momentum_rotation
from src.strategies import (
    weights_momentum_low_vol_score,
    weights_risk_parity,
    weights_sma_crossover,
    weights_trend_filtered_momentum,
)


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


def test_trend_filtered_momentum_can_move_to_cash_when_scores_are_negative():
    dates = pd.date_range("2023-01-31", periods=15, freq="ME")
    prices = pd.DataFrame(
        {
            "A": [100.0 * (0.98**i) for i in range(15)],
            "B": [100.0 * (0.99**i) for i in range(15)],
        },
        index=dates,
    )

    weights = weights_trend_filtered_momentum(prices, top_n=1, min_score=0.0)

    assert weights.loc[dates[-1]].sum() == 0.0


def test_momentum_rotation_supports_inverse_vol_weighting():
    dates = pd.date_range("2023-01-31", periods=15, freq="ME")
    prices = pd.DataFrame(
        {
            "LOW_VOL": [100.0 * (1.01**i) for i in range(15)],
            "HIGH_VOL": [100.0, 120.0, 96.0, 130.0, 90.0, 140.0, 88.0, 145.0, 85.0, 150.0, 82.0, 155.0, 80.0, 160.0, 78.0],
        },
        index=dates,
    )

    weights = weights_momentum_rotation(prices, lookback=3, skip=1, top_n=2, weighting="inverse_vol", vol_lookback=6)

    assert round(weights.loc[dates[-1]].sum(), 6) == 1.0
    assert weights.loc[dates[-1], "LOW_VOL"] > weights.loc[dates[-1], "HIGH_VOL"]


def test_risk_parity_weights_sum_to_one_after_lookback_window():
    dates = pd.date_range("2023-01-31", periods=15, freq="ME")
    prices = pd.DataFrame(
        {
            "A": [100.0 * (1.01**i) for i in range(15)],
            "B": [100.0 * (1.02**i) for i in range(15)],
        },
        index=dates,
    )

    weights = weights_risk_parity(prices, lookback=6)

    assert round(weights.loc[dates[-1]].sum(), 6) == 1.0


def test_momentum_low_vol_score_selects_balanced_top_assets():
    dates = pd.date_range("2023-01-31", periods=15, freq="ME")
    prices = pd.DataFrame(
        {
            "TRENDY": [100.0 * (1.03**i) for i in range(15)],
            "STEADY": [100.0 * (1.01**i) for i in range(15)],
            "WEAK": [100.0 * (0.99**i) for i in range(15)],
        },
        index=dates,
    )

    weights = weights_momentum_low_vol_score(prices, momentum_lookback=3, momentum_skip=1, vol_lookback=6, top_n=2)

    assert round(weights.loc[dates[-1]].sum(), 6) == 1.0
    assert weights.loc[dates[-1], "WEAK"] == 0.0


def test_sma_crossover_accepts_custom_windows():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    close = pd.Series([1.0, 1.0, 2.0, 3.0, 4.0], index=dates, name="AAA")

    weights = weights_sma_crossover(close, short_window=2, long_window=3)

    assert weights.loc[dates[-1], "AAA"] == 1.0
