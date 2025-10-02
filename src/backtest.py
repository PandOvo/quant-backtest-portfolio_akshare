import numpy as np
import pandas as pd
from .config import COST_BPS

def backtest_weights(close: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    close = close.sort_index().ffill().dropna()
    weights = weights.reindex(close.index).ffill().fillna(0.0)
    rets = close.pct_change().fillna(0.0)

    w_prev = weights.shift(1).fillna(0.0)
    turnover = (weights - w_prev).abs().sum(axis=1)
    tc = turnover * (COST_BPS / 1e4)

    port_ret_gross = (rets * w_prev).sum(axis=1)
    port_ret_net = port_ret_gross - tc
    nav = (1 + port_ret_net).cumprod()
    dd = nav / nav.cummax() - 1.0

    out = pd.DataFrame({
        "port_ret_gross": port_ret_gross,
        "turnover": turnover,
        "tc": tc,
        "port_ret": port_ret_net,
        "nav": nav,
        "dd": dd
    }, index=close.index)
    return out
