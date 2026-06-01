from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config as defaults


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
        "sma": {"enabled": True, "short_window": defaults.SMA_SHORT, "long_window": defaults.SMA_LONG},
        "momentum": {"enabled": True, "lookback": defaults.MOM_LOOKBACK, "skip": defaults.MOM_SKIP, "top_n": defaults.MOM_TOP_N},
        "low_volatility": {"enabled": True, "lookback": 60, "top_n": 1},
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
            merged[name] = {**merged.get(name, {}), **(value or {})}
        cfg.strategies = merged

    return cfg

