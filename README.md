
# 量化回测示例（TuShare 数据源） Quant Backtest with TuShare

> 使用 **TuShare** 获取中国市场（ETF/指数/个股）真实历史数据，构建 **双均线交叉** 与 **12-1 动量轮动** 策略，评估绩效并输出图表与报表。

## 运行步骤
```bash
pip install -r requirements.txt
# Windows：先设置环境变量（重开终端生效）
setx TUSHARE_TOKEN "你的token"
python main.py
```

## 目录结构
```
quant-backtest-portfolio_tushare/
├─ data/                    # 本地CSV缓存（自动生成）
│  └─ .gitkeep
├─ output/
│  ├─ figures/              # 净值曲线、回撤曲线(PNG)
│  │  └─ .gitkeep
│  └─ reports/              # 指标表(CSV)
│     └─ .gitkeep
├─ src/
│  ├─ config.py             # 参数（标的池、窗口、成本等）
│  ├─ data.py               # 数据获取（TuShare）
│  ├─ strategies.py         # 策略（SMA/动量）
│  ├─ backtest.py           # 向量化回测与交易成本
│  ├─ metrics.py            # 绩效指标（中文列名）
│  └─ plotting.py           # 图表输出（中文标题）
├─ main.py                  # 一键运行
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## 注意事项
- 标的代码需为 **ts_code** 形如 `510300.SH`, `159915.SZ`, `000300.SH`；
- 首次运行会下载并缓存数据；之后会直接读取 `data/*.csv`；
- 本项目仅用于学习展示，不构成投资建议。
