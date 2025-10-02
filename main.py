import os
import pandas as pd
from src.config import (
    ASSETS_MOMENTUM, BASELINE, START, END,
    OUTPUT_FIG_DIR, OUTPUT_REP_DIR
)
from src.data import get_close_series, get_panel
from src.strategies import weights_sma_crossover, weights_momentum_rotation
from src.backtest import backtest_weights
from src.metrics import summary_table, max_drawdown
from src.plotting import plot_equity, plot_drawdown

def run_sma_example():
    s = get_close_series(BASELINE, start=START, end=END)
    w = weights_sma_crossover(s)
    close = pd.concat([s, pd.Series(1.0, index=s.index, name="CASH")], axis=1)
    res = backtest_weights(close, w)
    mdd, dd = max_drawdown(res["nav"])
    plot_equity(res["nav"], save_path=os.path.join(OUTPUT_FIG_DIR, "sma_净值.png"), title="双均线交叉策略 - 净值曲线")
    plot_drawdown(dd, save_path=os.path.join(OUTPUT_FIG_DIR, "sma_回撤.png"), title="双均线交叉策略 - 回撤曲线")
    met = summary_table(res)
    met.to_csv(os.path.join(OUTPUT_REP_DIR, "sma_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met

def run_momentum_example():
    close = get_panel(ASSETS_MOMENTUM, start=START, end=END).dropna(how="all")
    w = weights_momentum_rotation(close)
    res = backtest_weights(close, w)
    # 基准
    base = get_close_series(BASELINE, start=START, end=END)
    baseline_nav = (base.pct_change().fillna(0) + 1).cumprod()
    plot_equity(res["nav"], baseline_nav=baseline_nav.reindex(res.index), 
                save_path=os.path.join(OUTPUT_FIG_DIR, "动量_净值.png"), title="12-1 动量轮动（Top 2） - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(OUTPUT_FIG_DIR, "动量_回撤.png"), title="12-1 动量轮动（Top 2） - 回撤曲线")
    met = summary_table(res)
    met.to_csv(os.path.join(OUTPUT_REP_DIR, "动量_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met

if __name__ == "__main__":
    os.makedirs(OUTPUT_FIG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_REP_DIR, exist_ok=True)
    sma_res, sma_met = run_sma_example()
    mom_res, mom_met = run_momentum_example()
    all_metrics = pd.concat([
        sma_met.assign(策略="双均线交叉"),
        mom_met.assign(策略="12-1动量轮动Top2")
    ], ignore_index=True)
    cols = ["策略"] + [c for c in all_metrics.columns if c != "策略"]
    all_metrics = all_metrics[cols]
    all_metrics.to_csv(os.path.join(OUTPUT_REP_DIR, "总览_指标汇总.csv"), index=False, encoding="utf-8-sig")
    print("✔ 完成：请查看 output/ 目录下的图表与指标报表。")
