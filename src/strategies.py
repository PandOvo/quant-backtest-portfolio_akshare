import numpy as np
import pandas as pd
from .config import SMA_SHORT, SMA_LONG, MOM_LOOKBACK, MOM_SKIP, MOM_TOP_N

def weights_sma_crossover(close: pd.Series, short_window=SMA_SHORT, long_window=SMA_LONG) -> pd.DataFrame:
    s = close.dropna()
    ma_s = s.rolling(short_window).mean()
    ma_l = s.rolling(long_window).mean()
    signal = (ma_s > ma_l).astype(int)
    w = pd.DataFrame(index=s.index, data={
        "ASSET": signal.astype(float),
        "CASH": 1 - signal.astype(float)
    })
    w.rename(columns={"ASSET": s.name}, inplace=True)
    return w[[s.name, "CASH"]]

def _mom_score(prices: pd.DataFrame, lookback=12, skip=1):
    m = prices.resample("ME").last().dropna(how="all")
    return m.shift(skip) / m.shift(lookback) - 1.0

def _to_daily_weights(close: pd.DataFrame, weights_list: list[pd.Series]) -> pd.DataFrame:
    if not weights_list:
        return pd.DataFrame(0.0, index=close.index, columns=close.columns)
    w_monthly = pd.DataFrame(weights_list).sort_index()
    return w_monthly.reindex(close.resample("D").last().index).ffill().reindex(close.index).fillna(0.0)


def _inverse_vol_weights(rets: pd.DataFrame, picks, end_loc: int, lookback: int) -> pd.Series:
    window_slice = slice(max(0, end_loc - lookback), end_loc)
    vol = rets.iloc[window_slice][list(picks)].std().replace(0, np.nan).dropna()
    if vol.empty:
        return pd.Series(1.0 / len(picks), index=picks)
    inv_vol = 1.0 / vol
    return inv_vol / inv_vol.sum()


def weights_momentum_rotation(
    close: pd.DataFrame,
    lookback=MOM_LOOKBACK,
    skip=MOM_SKIP,
    top_n=MOM_TOP_N,
    min_score=None,
    weighting="equal",
    vol_lookback=60,
) -> pd.DataFrame:
    score = _mom_score(close, lookback=lookback, skip=skip)
    rets = close.pct_change()
    monthly_dates = score.index
    weights_list = []
    for dt in monthly_dates:
        s = score.loc[dt].dropna()
        if min_score is not None:
            s = s[s > min_score]
        if s.empty:
            continue
        top = s.sort_values(ascending=False).head(top_n).index
        w = pd.Series(0.0, index=close.columns)
        if weighting == "inverse_vol":
            end_loc = close.index.searchsorted(dt)
            w.loc[top] = _inverse_vol_weights(rets, top, end_loc, vol_lookback)
        else:
            w.loc[top] = 1.0 / len(top)
        w.name = dt
        weights_list.append(w)
    return _to_daily_weights(close, weights_list)


def weights_trend_filtered_momentum(
    close: pd.DataFrame,
    lookback=MOM_LOOKBACK,
    skip=MOM_SKIP,
    top_n=MOM_TOP_N,
    min_score=0.0,
    vol_lookback=60,
) -> pd.DataFrame:
    return weights_momentum_rotation(
        close,
        lookback=lookback,
        skip=skip,
        top_n=top_n,
        min_score=min_score,
        weighting="inverse_vol",
        vol_lookback=vol_lookback,
    )

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

    return _to_daily_weights(close, weights_list)


def weights_risk_parity(close: pd.DataFrame, lookback=120) -> pd.DataFrame:
    rets = close.pct_change()
    rebal_dates = _monthly_index_like(close)
    weights_list = []

    for dt in rebal_dates:
        end_loc = close.index.searchsorted(dt)
        if end_loc <= lookback:
            continue
        vol = rets.iloc[end_loc - lookback:end_loc].std().replace(0, np.nan).dropna()
        if vol.empty:
            continue
        inv_vol = 1.0 / vol
        w = pd.Series(0.0, index=close.columns)
        w.loc[inv_vol.index] = inv_vol / inv_vol.sum()
        w.name = dt
        weights_list.append(w)

    return _to_daily_weights(close, weights_list)


def weights_momentum_low_vol_score(
    close: pd.DataFrame,
    momentum_lookback=12,
    momentum_skip=1,
    vol_lookback=60,
    top_n=MOM_TOP_N,
    momentum_weight=0.6,
) -> pd.DataFrame:
    score = _mom_score(close, lookback=momentum_lookback, skip=momentum_skip)
    rets = close.pct_change()
    weights_list = []

    for dt in score.index:
        end_loc = close.index.searchsorted(dt)
        if end_loc <= vol_lookback:
            continue
        mom = score.loc[dt].dropna()
        vol = rets.iloc[end_loc - vol_lookback:end_loc].std().dropna()
        common = mom.index.intersection(vol.index)
        if common.empty:
            continue

        mom_rank = mom.loc[common].rank(pct=True)
        low_vol_rank = (-vol.loc[common]).rank(pct=True)
        combined = momentum_weight * mom_rank + (1.0 - momentum_weight) * low_vol_rank
        picks = combined.sort_values(ascending=False).head(top_n).index
        w = pd.Series(0.0, index=close.columns)
        w.loc[picks] = 1.0 / len(picks)
        w.name = dt
        weights_list.append(w)

    return _to_daily_weights(close, weights_list)


# ==== 计算月度收益序列（热力图） ====
def monthly_returns(daily_ret: pd.Series) -> pd.Series:
    return (1.0 + daily_ret).resample("ME").prod() - 1.0
