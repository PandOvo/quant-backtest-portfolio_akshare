import os
import pandas as pd
from src.config import (
    ASSETS_MOMENTUM, BASELINE, START, END,
    OUTPUT_FIG_DIR, OUTPUT_REP_DIR
)
from src.data import get_close_series, get_panel
from src.strategies import (
    weights_sma_crossover, weights_momentum_rotation,
    weights_low_volatility, monthly_returns   # <-- ADD
)
from src.backtest import backtest_weights
from src.metrics import summary_table, max_drawdown
from src.plotting import (
    plot_equity, plot_drawdown,
    plot_excess_return, plot_monthly_heatmap, plot_weights_area  # <-- ADD
)

def run_sma_example():
    s = get_close_series(BASELINE, start=START, end=END)
    w = weights_sma_crossover(s)
    close = pd.concat([s, pd.Series(1.0, index=s.index, name="CASH")], axis=1)
    res = backtest_weights(close, w)
    mdd, dd = max_drawdown(res["nav"])
    plot_equity(res["nav"], save_path=os.path.join(OUTPUT_FIG_DIR, "sma_净值.png"), title="双均线交叉策略 - 净值曲线")
    plot_drawdown(dd, save_path=os.path.join(OUTPUT_FIG_DIR, "sma_回撤.png"), title="双均线交叉策略 - 回撤曲线")
    met = summary_table(res)
    # 中文不乱码
    met.to_csv(os.path.join(OUTPUT_REP_DIR, "sma_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met

def run_momentum_example(close_panel=None):
    close = close_panel if close_panel is not None else get_panel(ASSETS_MOMENTUM, start=START, end=END).dropna(how="all")
    w = weights_momentum_rotation(close)
    res = backtest_weights(close, w)
    # 基准
    base = get_close_series(BASELINE, start=START, end=END)
    baseline_nav = (base.pct_change().fillna(0) + 1).cumprod()
    plot_equity(res["nav"], baseline_nav=baseline_nav.reindex(res.index),
                save_path=os.path.join(OUTPUT_FIG_DIR, "动量_净值.png"), title="12-1 动量轮动（Top 1/2） - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(OUTPUT_FIG_DIR, "动量_回撤.png"), title="12-1 动量轮动 - 回撤曲线")
    # 超额收益 & 权重
    plot_excess_return(res["nav"], baseline_nav.reindex(res.index),
                       save_path=os.path.join(OUTPUT_FIG_DIR, "动量_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(OUTPUT_FIG_DIR, "动量_持仓权重.png"))
    # 月度收益热力图
    mom_monthly = monthly_returns(res["port_ret"])
    plot_monthly_heatmap(mom_monthly, save_path=os.path.join(OUTPUT_FIG_DIR, "动量_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(OUTPUT_REP_DIR, "动量_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w

# ==== 低波动策略 ====
def run_lowvol_example(close_panel=None):
    close = close_panel if close_panel is not None else get_panel(ASSETS_MOMENTUM, start=START, end=END).dropna(how="all")
    w = weights_low_volatility(close, lookback=60, top_n=1)  # 过去 60 日波动率最小的 1 只
    res = backtest_weights(close, w)
    # 基准
    base = get_close_series(BASELINE, start=START, end=END)
    baseline_nav = (base.pct_change().fillna(0) + 1).cumprod()
    # 图表
    plot_equity(res["nav"], baseline_nav=baseline_nav.reindex(res.index),
                save_path=os.path.join(OUTPUT_FIG_DIR, "低波_净值.png"), title="低波动（60日最低波动 Top1） - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(OUTPUT_FIG_DIR, "低波_回撤.png"), title="低波动 - 回撤曲线")
    plot_excess_return(res["nav"], baseline_nav.reindex(res.index),
                       save_path=os.path.join(OUTPUT_FIG_DIR, "低波_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(OUTPUT_FIG_DIR, "低波_持仓权重.png"))
    # 月度热力图
    lv_monthly = monthly_returns(res["port_ret"])
    plot_monthly_heatmap(lv_monthly, save_path=os.path.join(OUTPUT_FIG_DIR, "低波_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(OUTPUT_REP_DIR, "低波_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w

if __name__ == "__main__":
    os.makedirs(OUTPUT_FIG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_REP_DIR, exist_ok=True)


    panel = get_panel(ASSETS_MOMENTUM, start=START, end=END).dropna(how="all")

    sma_res, sma_met = run_sma_example()
    mom_res, mom_met, mom_w = run_momentum_example(panel)
    lv_res,  lv_met,  lv_w  = run_lowvol_example(panel)

    base = get_close_series(BASELINE, start=START, end=END)
    baseline_nav = (base.pct_change().fillna(0) + 1).cumprod()

    # 汇总表
    all_metrics = pd.concat([
        sma_met.assign(策略="双均线交叉"),
        mom_met.assign(策略="12-1动量Top1/2"),
        lv_met.assign(策略="低波动Top1")
    ], ignore_index=True)
    cols = ["策略"] + [c for c in all_metrics.columns if c != "策略"]
    all_metrics = all_metrics[cols]
    all_metrics.to_csv(os.path.join(OUTPUT_REP_DIR, "总览_指标汇总.csv"), index=False, encoding="utf-8-sig")

    print(" 回测完成，输出结果如下：\n"
          "【双均线交叉】\n"
          "  - 图表: sma_净值.png, sma_回撤.png\n"
          "  - 报表: sma_指标.csv\n\n"
          "【动量轮动】\n"
          "  - 图表: 动量_净值.png, 动量_回撤.png, 动量_超额收益.png, 动量_月度收益热力图.png, 动量_持仓权重.png\n"
          "  - 报表: 动量_指标.csv\n\n"
          "【低波动策略】\n"
          "  - 图表: 低波_净值.png, 低波_回撤.png, 低波_超额收益.png, 低波_月度收益热力图.png, 低波_持仓权重.png\n"
          "  - 报表: 低波_指标.csv\n\n"
          "【汇总报告】\n"
          "  - 报表: 总览_指标汇总.csv\n\n"
          f"输出目录：\n  图表 → {OUTPUT_FIG_DIR}\n  报表 → {OUTPUT_REP_DIR}")

