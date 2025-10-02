import os
import matplotlib.pyplot as plt
import matplotlib

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
