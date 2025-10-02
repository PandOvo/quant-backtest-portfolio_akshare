# 📈 Quant Backtest Portfolio — 量化投资策略回测项目

本项目演示了如何使用 **Python + AkShare 数据源** 搭建量化投资策略回测框架，涵盖数据获取、策略实现、绩效评估与可视化。  
适合展示在 **金融科技 / 数据分析岗位求职作品集** 中，突出本人在金融数据处理与量化研究方面的能力。  

---

## 📂 项目结构

```
quant-backtest-portfolio/
├── data/                # 本地缓存的行情数据（自动生成）
├── output/              # 策略运行结果
│   ├── figures/         # 收益曲线、回撤图
│   └── reports/         # 策略绩效指标 (CSV/Excel)
├── src/                 # 核心源码
│   ├── data.py          # 数据获取 (AkShare: 股票 / ETF)
│   ├── strategies.py    # 策略实现 (均线交叉 / 动量轮动)
│   ├── plotting.py      # 可视化绘图
│   └── config.py        # 参数配置（股票池、窗口期、路径等）
├── main.py              # 主程序入口
├── requirements.txt     # 依赖库
└── README.md            # 项目说明
```

---

## 🛠 技术栈

- **语言**: Python 3.8+  
- **数据源**: [AkShare](https://github.com/akfamily/akshare) （东方财富数据，免费，无需 Token）  
- **核心库**: `pandas`, `numpy`, `matplotlib`, `akshare`  
- **可视化**: 收益曲线、最大回撤曲线  

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/quant-backtest-portfolio.git
cd quant-backtest-portfolio
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置股票池
修改 `src/config.py`，例如：
```python
# 股票池示例（贵州茅台、平安银行、浦发银行）
ASSETS_MOMENTUM = ["600519.SH", "000001.SZ", "600000.SH"]
BASELINE = "600519.SH"
```

### 4. 运行回测
```bash
python main.py
```

### 5. 查看结果
- 策略图表：`output/figures/`  
- 策略指标：`output/reports/`  

---

## 📊 策略说明

1. **均线交叉策略（SMA Crossover）**  
   - 计算短期 / 长期均线  
   - 短期上穿长期 → 买入，短期下穿长期 → 卖出  

2. **动量轮动策略（Momentum Rotation）**  
   - 回看过去 12 个月收益率  
   - 每月调仓，选择收益率最高的 N 只股票/ETF  

---

## 📈 绩效指标

运行完成后会输出以下指标表（CSV/Excel）：
- 年化收益率  
- 夏普比率  
- 最大回撤  
- 胜率等  

同时配套 **净值曲线图 & 回撤曲线图**，便于直观展示。

---

## 🏆 项目亮点

- **实战导向**：基于真实市场数据（AkShare → 东方财富），非虚拟数据。  
- **完整闭环**：从数据 → 策略 → 绩效 → 可视化，一键运行。  
- **简洁清晰**：代码结构模块化，HR 即使不是量化专家也能理解。  

---

## 💡 为什么这个项目能体现我适合金融科技/数据分析岗位？

因为它展示了我能：  
1. 从 **真实金融数据源** 获取并清洗数据；  
2. 用 **Python** 搭建量化模型并实现策略逻辑；  
3. 通过 **绩效指标与可视化** 分析结果并输出结论。  

这正是金融科技和数据分析岗位需要的核心技能。  

---

## 🔮 未来改进方向

- 增加更多因子（估值、波动率等），构建多因子选股模型  
- 引入风险控制模块（止损、仓位管理）  
- 接入回测框架（如 backtrader、quantstats）提升扩展性  
- 支持更多市场（美股、期货、加密货币）  

---

✍️ **作者**: [你的名字/ID]  
📅 **时间**: 2025  
