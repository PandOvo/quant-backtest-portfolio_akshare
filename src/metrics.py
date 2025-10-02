import numpy as np
import pandas as pd

def annualize_return(daily_ret: pd.Series, freq=252):
    cum = (1 + daily_ret).prod()
    n = daily_ret.shape[0]
    if n == 0: return np.nan
    return cum ** (freq / n) - 1

def annualize_vol(daily_ret: pd.Series, freq=252):
    return daily_ret.std() * np.sqrt(freq)

def sharpe(daily_ret: pd.Series, rf=0.0, freq=252):
    er = daily_ret.mean() * freq - rf
    vol = annualize_vol(daily_ret, freq)
    return er / vol if vol and vol != 0 else np.nan

def max_drawdown(nav: pd.Series):
    roll_max = nav.cummax()
    dd = nav / roll_max - 1.0
    return dd.min(), dd

def calmar(daily_ret: pd.Series, nav: pd.Series):
    cagr = annualize_return(daily_ret)
    mdd, _ = max_drawdown(nav)
    return cagr / abs(mdd) if mdd and mdd != 0 else np.nan

def summary_table(port_df: pd.DataFrame) -> pd.DataFrame:
    daily = port_df["port_ret"]
    cagr = annualize_return(daily)
    vol = annualize_vol(daily)
    sr = sharpe(daily)
    mdd, _ = max_drawdown(port_df["nav"])
    cmr = calmar(daily, port_df["nav"])
    win_rate = (daily > 0).mean()
    turnover = port_df["turnover"].mean()
    return pd.DataFrame({
        "年化收益率": [cagr],
        "年化波动率": [vol],
        "夏普比率": [sr],
        "最大回撤": [mdd],
        "卡玛比率": [cmr],
        "胜率": [win_rate],
        "平均每日换手率": [turnover]
    })
