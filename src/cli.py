import argparse

from .config_loader import load_config
from .runner import run_backtest


def parse_args():
    parser = argparse.ArgumentParser(description="Run AkShare-powered A-share backtests.")
    parser.add_argument("--config", default="configs/demo.yaml", help="Path to a YAML config file.")
    parser.add_argument("--output-dir", help="Override the output directory.")
    parser.add_argument("--start", help="Override the backtest start date, for example 2018-01-01.")
    parser.add_argument("--end", help="Override the backtest end date, for example 2024-12-31.")
    parser.add_argument("--assets", nargs="+", help="Override the asset pool, for example 600519.SH 000001.SZ.")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = load_config(args.config)
    if args.output_dir:
        cfg.output_dir = args.output_dir
    if args.start:
        cfg.start = args.start
    if args.end:
        cfg.end = args.end
    if args.assets:
        cfg.assets = args.assets

    run_backtest(cfg)
    print(f"回测完成。图表目录: {cfg.output_fig_dir} | 报表目录: {cfg.output_rep_dir}")


if __name__ == "__main__":
    main()
