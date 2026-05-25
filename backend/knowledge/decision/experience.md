# Decision 经验文档

## 范围
把所有 Analyst 的 Judgment + Simulator 的 Trajectory → 农户/B 端能直接执行的预警。
本文件由 Harness 持续追加；下游生成预警时会**同时叠加** `seed/mock/experience.md` 中的历史 CASE 库。

## 关键原则
- 风险等级 = max(领域 Judgment) → 再被 Crop 脆弱度和 Plot 暴露度上调
- 任何高风险 actions 必须含 (1) 具体药剂/操作 (2) 时间窗口 (3) 复查节点
- 给保险公司的 payload 永远附 risk_score + claim_intent_id + matched_history_case
- 复合场景（玉米拔节/抽雄/灌浆 + 湿土壤 + 大风）直接判定为倒伏高风险

## 历史教训（Harness 会持续往这里追加）

### 漏报案例：玉米·倒伏·2025 东北（基线种子）
- 复合场景：拔节期 + 土壤湿度 ≥ 0.4 + 6 级大风 持续 3h
- 单领域看都只是"中风险"，复合后是"高风险"
- 下次见到 (jointing OR tasseling) AND (湿度 ≥0.38) AND (风 ≥12 m/s 持续 3h+) → 直接判定为高
