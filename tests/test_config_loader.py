from pathlib import Path

from src.config_loader import load_config


def test_load_config_merges_yaml_with_defaults(tmp_path):
    cfg_path = Path(tmp_path) / "demo.yaml"
    cfg_path.write_text(
        """
assets:
  - 510300.SH
baseline: 510300.SH
output_dir: output/test
strategies:
  momentum:
    top_n: 1
  low_volatility:
    enabled: false
""",
        encoding="utf-8",
    )

    cfg = load_config(str(cfg_path))

    assert cfg.assets == ["510300.SH"]
    assert cfg.baseline == "510300.SH"
    assert Path(cfg.output_fig_dir).parts[-3:] == ("output", "test", "figures")
    assert cfg.strategies["momentum"]["lookback"] == 12
    assert cfg.strategies["momentum"]["top_n"] == 1
    assert cfg.strategies["low_volatility"]["enabled"] is False
