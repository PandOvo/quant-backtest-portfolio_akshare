import os

import pandas as pd

from .backtest import backtest_weights
from .config_loader import BacktestConfig, load_config
from .data import get_close_series, get_panel
from .metrics import max_drawdown, summary_table
from .plotting import plot_drawdown, plot_equity, plot_excess_return, plot_monthly_heatmap, plot_weights_area
from .strategies import monthly_returns, weights_low_volatility, weights_momentum_rotation, weights_sma_crossover


def _strategy_enabled(cfg: BacktestConfig, name: str) -> bool:
    return cfg.strategies.get(name, {}).get("enabled", True)


def _baseline_nav(cfg: BacktestConfig, index) -> pd.Series:
    base = get_close_series(cfg.baseline, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir)
    nav = (base.pct_change().fillna(0) + 1).cumprod()
    return nav.reindex(index)


def run_sma(cfg: BacktestConfig):
    params = cfg.strategies.get("sma", {})
    s = get_close_series(cfg.baseline, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir)
    w = weights_sma_crossover(
        s,
        short_window=params.get("short_window", 20),
        long_window=params.get("long_window", 60),
    )
    close = pd.concat([s, pd.Series(1.0, index=s.index, name="CASH")], axis=1)
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    _, dd = max_drawdown(res["nav"])
    plot_equity(res["nav"], save_path=os.path.join(cfg.output_fig_dir, "sma_净值.png"), title="双均线交叉策略 - 净值曲线")
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "sma_回撤.png"), title="双均线交叉策略 - 回撤曲线")
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "sma_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met


def run_momentum(cfg: BacktestConfig, close_panel=None):
    params = cfg.strategies.get("momentum", {})
    close = close_panel if close_panel is not None else get_panel(
        cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir
    ).dropna(how="all")
    w = weights_momentum_rotation(
        close,
        lookback=params.get("lookback", 12),
        skip=params.get("skip", 1),
        top_n=params.get("top_n", 2),
    )
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    baseline_nav = _baseline_nav(cfg, res.index)
    plot_equity(res["nav"], baseline_nav=baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "动量_净值.png"), title="12-1 动量轮动 - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "动量_回撤.png"), title="12-1 动量轮动 - 回撤曲线")
    plot_excess_return(res["nav"], baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "动量_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(cfg.output_fig_dir, "动量_持仓权重.png"))
    plot_monthly_heatmap(monthly_returns(res["port_ret"]), save_path=os.path.join(cfg.output_fig_dir, "动量_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "动量_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w


def run_low_volatility(cfg: BacktestConfig, close_panel=None):
    params = cfg.strategies.get("low_volatility", {})
    close = close_panel if close_panel is not None else get_panel(
        cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir
    ).dropna(how="all")
    w = weights_low_volatility(close, lookback=params.get("lookback", 60), top_n=params.get("top_n", 1))
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    baseline_nav = _baseline_nav(cfg, res.index)
    plot_equity(res["nav"], baseline_nav=baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "低波_净值.png"), title="低波动策略 - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "低波_回撤.png"), title="低波动 - 回撤曲线")
    plot_excess_return(res["nav"], baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "低波_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(cfg.output_fig_dir, "低波_持仓权重.png"))
    plot_monthly_heatmap(monthly_returns(res["port_ret"]), save_path=os.path.join(cfg.output_fig_dir, "低波_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "低波_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w


def run_backtest(cfg: BacktestConfig) -> pd.DataFrame:
    os.makedirs(cfg.output_fig_dir, exist_ok=True)
    os.makedirs(cfg.output_rep_dir, exist_ok=True)

    panel = get_panel(cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir).dropna(how="all")
    metrics = []

    if _strategy_enabled(cfg, "sma"):
        _, sma_met = run_sma(cfg)
        metrics.append(sma_met.assign(策略="双均线交叉"))
    if _strategy_enabled(cfg, "momentum"):
        _, mom_met, _ = run_momentum(cfg, panel)
        metrics.append(mom_met.assign(策略="12-1动量"))
    if _strategy_enabled(cfg, "low_volatility"):
        _, lv_met, _ = run_low_volatility(cfg, panel)
        metrics.append(lv_met.assign(策略="低波动"))

    all_metrics = pd.concat(metrics, ignore_index=True)
    all_metrics = all_metrics[["策略"] + [c for c in all_metrics.columns if c != "策略"]]
    all_metrics.to_csv(os.path.join(cfg.output_rep_dir, "总览_指标汇总.csv"), index=False, encoding="utf-8-sig")
    return all_metrics


def main(config_path: str | None = None) -> pd.DataFrame:
    cfg = load_config(config_path)
    result = run_backtest(cfg)
    print(f"回测完成。图表目录: {cfg.output_fig_dir} | 报表目录: {cfg.output_rep_dir}")
    return result

