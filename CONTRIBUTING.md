# Contributing

欢迎提交 issue、策略想法、测试用例和 PR。

## 推荐贡献方向

- 新策略：ETF 轮动、行业轮动、定投择时、多因子组合
- 新指标：信息比率、Alpha/Beta、分年度收益、换手成本拆解
- 新报告：参数扫描热力图、策略对比仪表盘、Streamlit 页面
- 工程增强：可安装 CLI、更多测试、数据源容错

## 本地验证

```bash
pip install -r requirements.txt
pytest
python main.py
```

## PR 建议

- 保持改动聚焦
- 新策略请补测试和 README 说明
- 不要提交大体积临时数据
- 回测结果仅作为研究样例，不要写成投资建议
