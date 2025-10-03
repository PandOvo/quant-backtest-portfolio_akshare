import numpy as np
import pandas as pd
from .config import SMA_SHORT, SMA_LONG, MOM_LOOKBACK, MOM_SKIP, MOM_TOP_N

def weights_sma_crossover(close: pd.Series) -> pd.DataFrame:
    s = close.dropna()
    ma_s = s.rolling(SMA_SHORT).mean()
    ma_l = s.rolling(SMA_LONG).mean()
    signal = (ma_s > ma_l).astype(int)
    w = pd.DataFrame(index=s.index, data={
        "ASSET": signal.astype(float),
        "CASH": 1 - signal.astype(float)
    })
    w.rename(columns={"ASSET": s.name}, inplace=True)
    return w[[s.name, "CASH"]]

def _mom_score(prices: pd.DataFrame, lookback=12, skip=1):
    m = prices.resample("ME").last().dropna(how="all")
    ret = m.pct_change(lookback) - m.pct_change(skip)
    score = ret.shift(1)
    return score

def weights_momentum_rotation(close: pd.DataFrame, top_n=MOM_TOP_N) -> pd.DataFrame:
    score = _mom_score(close, lookback=MOM_LOOKBACK, skip=MOM_SKIP)
    monthly_dates = score.index
    weights_list = []
    for dt in monthly_dates:
        s = score.loc[dt].dropna()
        if s.empty:
            continue
        top = s.sort_values(ascending=False).head(top_n).index
        w = pd.Series(0.0, index=close.columns)
        w.loc[top] = 1.0 / len(top)
        w.name = dt
        weights_list.append(w)
    w_monthly = pd.DataFrame(weights_list).sort_index()
    w_daily = w_monthly.reindex(close.resample("D").last().index).ffill().reindex(close.index).fillna(0.0)
    return w_daily

def _monthly_index_like(prices: pd.DataFrame) -> pd.DatetimeIndex:

    return prices.resample("ME").last().index

def weights_low_volatility(close: pd.DataFrame, lookback=60, top_n=None) -> pd.DataFrame:

    if top_n is None:
        top_n = MOM_TOP_N

    rets = close.pct_change()
    # 月末调仓点
    rebal_dates = _monthly_index_like(close)
    weights_list = []

    for dt in rebal_dates:

        end_loc = close.index.searchsorted(dt)
        if end_loc <= lookback:
            continue
        window_slice = slice(end_loc - lookback, end_loc)
        vol = rets.iloc[window_slice].std()
        vol = vol.dropna()
        if vol.empty:
            continue
        picks = vol.nsmallest(min(top_n, len(vol))).index
        w = pd.Series(0.0, index=close.columns)
        w.loc[picks] = 1.0 / len(picks)
        w.name = dt
        weights_list.append(w)

    if not weights_list:
        return pd.DataFrame(0.0, index=close.index, columns=close.columns)

    w_monthly = pd.DataFrame(weights_list).sort_index()
    w_daily = w_monthly.reindex(close.resample("D").last().index).ffill().reindex(close.index).fillna(0.0)
    return w_daily


# ==== 计算月度收益序列（热力图） ====
def monthly_returns(daily_ret: pd.Series) -> pd.Series:
    return (1.0 + daily_ret).resample("ME").prod() - 1.0
