import os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd

matplotlib.rcParams['font.sans-serif'] = [
    'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Hiragino Sans GB',
    'Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'Arial Unicode MS'
]
matplotlib.rcParams['axes.unicode_minus'] = False

def _ensure_dir(d): os.makedirs(d, exist_ok=True)

def plot_equity(nav, baseline_nav=None, save_path=None, title="策略净值曲线"):
    plt.figure(figsize=(10,5))
    nav.plot(label="策略净值")
    if baseline_nav is not None:
        baseline_nav.plot(label="基准净值", alpha=0.7)
    plt.legend(); plt.title(title); plt.xlabel("日期"); plt.ylabel("净值")
    if save_path:
        _ensure_dir(os.path.dirname(save_path))
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

def plot_drawdown(dd, save_path=None, title="回撤曲线"):
    plt.figure(figsize=(10,3.2))
    dd.plot()
    plt.title(title); plt.xlabel("日期"); plt.ylabel("回撤")
    if save_path:
        _ensure_dir(os.path.dirname(save_path))
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

def plot_excess_return(nav, baseline_nav, save_path=None, title="超额收益（策略-基准）"):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10,3.2))
    excess = nav.reindex(baseline_nav.index) - baseline_nav
    excess.plot()
    plt.title(title); plt.xlabel("日期"); plt.ylabel("超额净值差")
    if save_path:
        _ensure_dir(os.path.dirname(save_path))
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

def plot_monthly_heatmap(monthly_ret, save_path=None, title="月度收益热力图"):

    df = monthly_ret.copy()
    if isinstance(df, pd.Series):
        df = df.to_frame("ret")

    df["Year"] = df.index.year
    df["Month"] = df.index.month
    pivot = df.pivot_table(index="Year", columns="Month", values=df.columns[0], aggfunc="mean")

    for m in range(1,13):
        if m not in pivot.columns:
            pivot[m] = np.nan
    pivot = pivot[sorted(pivot.columns)]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn", vmin=-pivot.abs().max().max(), vmax=pivot.abs().max().max())
    ax.set_title(title)
    ax.set_xlabel("月份")
    ax.set_ylabel("年份")
    ax.set_xticks(range(12)); ax.set_xticklabels(range(1,13))
    ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index)

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if np.isfinite(val):
                ax.text(j, i, f"{val*100:.1f}%", va="center", ha="center", fontsize=8, color="black")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="月收益")
    if save_path:
        _ensure_dir(os.path.dirname(save_path))
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

def plot_weights_area(weights_df, save_path=None, title="持仓权重随时间变化"):
    cols = list(weights_df.columns)
    x = weights_df.index
    y = weights_df[cols].T.values  # shape: n_assets x T

    plt.figure(figsize=(10, 4))
    plt.stackplot(x, y, labels=cols, alpha=0.9)
    plt.legend(loc="upper left", ncol=min(len(cols), 4), fontsize=8)
    plt.title(title); plt.xlabel("日期"); plt.ylabel("权重")
    if save_path:
        _ensure_dir(os.path.dirname(save_path))
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
