import os

import pandas as pd

from .backtest import backtest_weights
from .config_loader import BacktestConfig, load_config
from .data import get_close_series, get_panel
from .metrics import max_drawdown, summary_table
from .plotting import plot_drawdown, plot_equity, plot_excess_return, plot_monthly_heatmap, plot_weights_area
from .strategies import (
    monthly_returns,
    weights_low_volatility,
    weights_momentum_rotation,
    weights_momentum_low_vol_score,
    weights_risk_parity,
    weights_enhanced_sma_crossover,
    weights_sma_crossover,
    weights_trend_filtered_momentum,
)


def _strategy_enabled(cfg: BacktestConfig, name: str) -> bool:
    return cfg.strategies.get(name, {}).get("enabled", True)


def _baseline_nav(cfg: BacktestConfig, index) -> pd.Series:
    base = get_close_series(cfg.baseline, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir)
    nav = (base.pct_change().fillna(0) + 1).cumprod()
    return nav.reindex(index)


def run_sma(cfg: BacktestConfig):
    params = cfg.strategies.get("sma", {})
    s = get_close_series(cfg.baseline, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir)
    run_sma_grid_search(cfg, s)
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


def run_sma_grid_search(cfg: BacktestConfig, close: pd.Series) -> pd.DataFrame | None:
    params = cfg.strategies.get("sma", {})
    grid = params.get("grid_search", {})
    if not grid.get("enabled", False):
        return None

    close_df = pd.concat([close, pd.Series(1.0, index=close.index, name="CASH")], axis=1)
    rows = []
    for short_window in grid.get("short_windows", [10, 20, 30]):
        for long_window in grid.get("long_windows", [50, 60, 120]):
            if short_window >= long_window:
                continue
            weights = weights_sma_crossover(close, short_window=short_window, long_window=long_window)
            result = backtest_weights(close_df, weights, cost_bps=cfg.cost_bps)
            metrics = summary_table(result).iloc[0].to_dict()
            metrics.update({"短均线": short_window, "长均线": long_window})
            rows.append(metrics)

    if not rows:
        return None

    report = pd.DataFrame(rows)
    objective = grid.get("objective", "夏普比率")
    if objective in report.columns:
        report = report.sort_values(objective, ascending=False)
    report = report[["短均线", "长均线"] + [c for c in report.columns if c not in ["短均线", "长均线"]]]
    report.to_csv(os.path.join(cfg.output_rep_dir, "双均线_参数扫描.csv"), index=False, encoding="utf-8-sig")
    return report


def run_enhanced_sma(cfg: BacktestConfig):
    params = cfg.strategies.get("enhanced_sma", {})
    s = get_close_series(cfg.baseline, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir)
    w = weights_enhanced_sma_crossover(
        s,
        short_window=params.get("short_window", 20),
        long_window=params.get("long_window", 60),
        band=params.get("band", 0.01),
        confirm_days=params.get("confirm_days", 3),
        require_long_ma_rising=params.get("require_long_ma_rising", True),
        slope_window=params.get("slope_window", 5),
        stop_loss_pct=params.get("stop_loss_pct", 0.08),
        trailing_stop_pct=params.get("trailing_stop_pct", 0.12),
        target_vol=params.get("target_vol", 0.18),
        vol_lookback=params.get("vol_lookback", 20),
        max_position=params.get("max_position", 1.0),
    )
    close = pd.concat([s, pd.Series(1.0, index=s.index, name="CASH")], axis=1)
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    _, dd = max_drawdown(res["nav"])
    plot_equity(res["nav"], save_path=os.path.join(cfg.output_fig_dir, "增强双均线_净值.png"), title="增强双均线策略 - 净值曲线")
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "增强双均线_回撤.png"), title="增强双均线策略 - 回撤曲线")
    plot_weights_area(w, save_path=os.path.join(cfg.output_fig_dir, "增强双均线_仓位.png"), title="增强双均线仓位")
    plot_monthly_heatmap(monthly_returns(res["port_ret"]), save_path=os.path.join(cfg.output_fig_dir, "增强双均线_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "增强双均线_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w


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
        weighting=params.get("weighting", "equal"),
        min_score=params.get("min_score"),
        vol_lookback=params.get("vol_lookback", 60),
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


def run_trend_momentum(cfg: BacktestConfig, close_panel=None):
    params = cfg.strategies.get("trend_momentum", {})
    close = close_panel if close_panel is not None else get_panel(
        cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir
    ).dropna(how="all")
    w = weights_trend_filtered_momentum(
        close,
        lookback=params.get("lookback", 12),
        skip=params.get("skip", 1),
        top_n=params.get("top_n", 2),
        min_score=params.get("min_score", 0.0),
        vol_lookback=params.get("vol_lookback", 60),
    )
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    baseline_nav = _baseline_nav(cfg, res.index)
    plot_equity(res["nav"], baseline_nav=baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "增强动量_净值.png"), title="趋势过滤动量 - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "增强动量_回撤.png"), title="趋势过滤动量 - 回撤曲线")
    plot_excess_return(res["nav"], baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "增强动量_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(cfg.output_fig_dir, "增强动量_持仓权重.png"))
    plot_monthly_heatmap(monthly_returns(res["port_ret"]), save_path=os.path.join(cfg.output_fig_dir, "增强动量_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "增强动量_指标.csv"), index=False, encoding="utf-8-sig")
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


def run_multi_factor(cfg: BacktestConfig, close_panel=None):
    params = cfg.strategies.get("multi_factor", {})
    close = close_panel if close_panel is not None else get_panel(
        cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir
    ).dropna(how="all")
    w = weights_momentum_low_vol_score(
        close,
        momentum_lookback=params.get("momentum_lookback", 12),
        momentum_skip=params.get("momentum_skip", 1),
        vol_lookback=params.get("vol_lookback", 60),
        top_n=params.get("top_n", 2),
        momentum_weight=params.get("momentum_weight", 0.6),
    )
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    baseline_nav = _baseline_nav(cfg, res.index)
    plot_equity(res["nav"], baseline_nav=baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "多因子_净值.png"), title="动量低波复合因子 - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "多因子_回撤.png"), title="动量低波复合因子 - 回撤曲线")
    plot_excess_return(res["nav"], baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "多因子_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(cfg.output_fig_dir, "多因子_持仓权重.png"))
    plot_monthly_heatmap(monthly_returns(res["port_ret"]), save_path=os.path.join(cfg.output_fig_dir, "多因子_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "多因子_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w


def run_risk_parity(cfg: BacktestConfig, close_panel=None):
    params = cfg.strategies.get("risk_parity", {})
    close = close_panel if close_panel is not None else get_panel(
        cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir
    ).dropna(how="all")
    w = weights_risk_parity(close, lookback=params.get("lookback", 120))
    res = backtest_weights(close, w, cost_bps=cfg.cost_bps)
    baseline_nav = _baseline_nav(cfg, res.index)
    plot_equity(res["nav"], baseline_nav=baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "风险平价_净值.png"), title="反波动率风险平价 - 净值曲线")
    _, dd = max_drawdown(res["nav"])
    plot_drawdown(dd, save_path=os.path.join(cfg.output_fig_dir, "风险平价_回撤.png"), title="反波动率风险平价 - 回撤曲线")
    plot_excess_return(res["nav"], baseline_nav, save_path=os.path.join(cfg.output_fig_dir, "风险平价_超额收益.png"))
    plot_weights_area(w, save_path=os.path.join(cfg.output_fig_dir, "风险平价_持仓权重.png"))
    plot_monthly_heatmap(monthly_returns(res["port_ret"]), save_path=os.path.join(cfg.output_fig_dir, "风险平价_月度收益热力图.png"))
    met = summary_table(res)
    met.to_csv(os.path.join(cfg.output_rep_dir, "风险平价_指标.csv"), index=False, encoding="utf-8-sig")
    return res, met, w


def run_backtest(cfg: BacktestConfig) -> pd.DataFrame:
    os.makedirs(cfg.output_fig_dir, exist_ok=True)
    os.makedirs(cfg.output_rep_dir, exist_ok=True)

    panel = get_panel(cfg.assets, start=cfg.start, end=cfg.end, adjust=cfg.adjust, cache_dir=cfg.cache_dir).dropna(how="all")
    metrics = []

    if _strategy_enabled(cfg, "sma"):
        _, sma_met = run_sma(cfg)
        metrics.append(sma_met.assign(策略="双均线交叉"))
    if _strategy_enabled(cfg, "enhanced_sma"):
        _, enhanced_sma_met, _ = run_enhanced_sma(cfg)
        metrics.append(enhanced_sma_met.assign(策略="增强双均线"))
    if _strategy_enabled(cfg, "momentum"):
        _, mom_met, _ = run_momentum(cfg, panel)
        metrics.append(mom_met.assign(策略="12-1动量"))
    if _strategy_enabled(cfg, "trend_momentum"):
        _, trend_met, _ = run_trend_momentum(cfg, panel)
        metrics.append(trend_met.assign(策略="趋势过滤动量"))
    if _strategy_enabled(cfg, "multi_factor"):
        _, mf_met, _ = run_multi_factor(cfg, panel)
        metrics.append(mf_met.assign(策略="动量低波多因子"))
    if _strategy_enabled(cfg, "low_volatility"):
        _, lv_met, _ = run_low_volatility(cfg, panel)
        metrics.append(lv_met.assign(策略="低波动"))
    if _strategy_enabled(cfg, "risk_parity"):
        _, rp_met, _ = run_risk_parity(cfg, panel)
        metrics.append(rp_met.assign(策略="风险平价"))

    all_metrics = pd.concat(metrics, ignore_index=True)
    all_metrics = all_metrics[["策略"] + [c for c in all_metrics.columns if c != "策略"]]
    all_metrics.to_csv(os.path.join(cfg.output_rep_dir, "总览_指标汇总.csv"), index=False, encoding="utf-8-sig")
    return all_metrics


def main(config_path: str | None = None) -> pd.DataFrame:
    cfg = load_config(config_path)
    result = run_backtest(cfg)
    print(f"回测完成。图表目录: {cfg.output_fig_dir} | 报表目录: {cfg.output_rep_dir}")
    return result
