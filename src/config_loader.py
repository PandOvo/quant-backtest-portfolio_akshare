from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config as defaults


def _deep_merge(base: dict, override: dict) -> dict:
    merged = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@dataclass
class BacktestConfig:
    assets: list[str] = field(default_factory=lambda: list(defaults.ASSETS_MOMENTUM))
    baseline: str = defaults.BASELINE
    start: str = defaults.START
    end: str | None = defaults.END
    cost_bps: float = defaults.COST_BPS
    cache_dir: str = defaults.CACHE_DIR
    output_dir: str = "output"
    adjust: str = "qfq"
    strategies: dict = field(default_factory=lambda: {
        "sma": {
            "enabled": True,
            "short_window": defaults.SMA_SHORT,
            "long_window": defaults.SMA_LONG,
            "grid_search": {
                "enabled": True,
                "short_windows": [10, 20, 30],
                "long_windows": [50, 60, 120],
                "objective": "夏普比率",
            },
        },
        "enhanced_sma": {
            "enabled": True,
            "short_window": defaults.SMA_SHORT,
            "long_window": defaults.SMA_LONG,
            "band": 0.01,
            "confirm_days": 3,
            "require_long_ma_rising": True,
            "slope_window": 5,
            "stop_loss_pct": 0.08,
            "trailing_stop_pct": 0.12,
            "target_vol": 0.18,
            "vol_lookback": 20,
            "max_position": 1.0,
        },
        "momentum": {"enabled": True, "lookback": defaults.MOM_LOOKBACK, "skip": defaults.MOM_SKIP, "top_n": defaults.MOM_TOP_N},
        "trend_momentum": {"enabled": True, "lookback": defaults.MOM_LOOKBACK, "skip": defaults.MOM_SKIP, "top_n": defaults.MOM_TOP_N, "min_score": 0.0, "vol_lookback": 60},
        "multi_factor": {"enabled": True, "momentum_lookback": defaults.MOM_LOOKBACK, "momentum_skip": defaults.MOM_SKIP, "vol_lookback": 60, "top_n": defaults.MOM_TOP_N, "momentum_weight": 0.6},
        "low_volatility": {"enabled": True, "lookback": 60, "top_n": 1},
        "risk_parity": {"enabled": True, "lookback": 120},
    })

    @property
    def output_fig_dir(self) -> str:
        return str(Path(self.output_dir) / "figures")

    @property
    def output_rep_dir(self) -> str:
        return str(Path(self.output_dir) / "reports")


def load_config(path: str | None = None) -> BacktestConfig:
    cfg = BacktestConfig()
    if not path:
        return cfg

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    for key in ["assets", "baseline", "start", "end", "cost_bps", "cache_dir", "output_dir", "adjust"]:
        if key in raw:
            setattr(cfg, key, raw[key])

    if "strategies" in raw:
        merged = cfg.strategies.copy()
        for name, value in (raw["strategies"] or {}).items():
            merged[name] = _deep_merge(merged.get(name, {}), value or {})
        cfg.strategies = merged

    return cfg
