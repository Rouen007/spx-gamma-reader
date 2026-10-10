# 证据与连续截图台账

工具不验证行情真假，不自动判断机会。图上时点缺失可记录收图时间 received_at，但 evidence_at 保留 null，不能用于可执行确认。

## 单次记录

详见 `../../examples/observation.json`（合成数据）。

- `record_id`：不可重复；`decision_at`：带时区的决策截止。
- `evidence[]`：id、instrument、contract、session_date、source、chart_type、evidence_at、received_at、settings、observations。SPX contract 可为 null；ES 必须明确合约或标 unknown。
- `mode`：`observation` 允许缺时间；`decision` 要求引用证据的时间与 session 可核验。
- `used_evidence_ids`：本次实际引用的证据。
- `cross_instrument_alignment`：`separate` 分开解读，或 `basis` 用配对报价换算。
- `basis`：需要时保存 spot/futures、合约、两边时间、source、value，约定 `ES - SPX`。
- `cvd_comparisons[]`：设置相同且 known 才比较；记录范围、起点、过滤和重置。
- `hypothesis`：候选区、观察、价格确认、等待、触发、失效、第一目标；未知用 null，不填虚构价格。

固定几分钟不是通用新鲜度。使用者需记录可容忍时差与来源更新机制。`basis_max_skew_seconds` 是配对报价之间的容忍时差，`basis_max_age_seconds` 是相对决策时点的最大报价年龄；二者必须显式声明，是本次换算假设，不是通用阈值。

## 追加

```sh
python3 spx-gamma-reader/scripts/ledger.py check examples/observation.json
python3 spx-gamma-reader/scripts/ledger.py append record.json --ledger local-evidence/session.jsonl
```

重复 record_id 拒绝，不改旧行。修正用新 record_id 和 `supersedes` 指向旧记录，并写原因。相同截图保留去重关联，不制造独立样本。

## 复盘

冻结当时证据及假设，再加后续结果：未触发、触发后目标先到、失效先到、未解决。没有 K线 OHLC 不确认精确回踩或止损顺序，不把缺失路径画成连续观察。

候选区移动说明是节点迁移、挂单变化还是价格确认变化；原地亮度变化另记。真实成交需合约、报价、成本和成交证明，模拟界面或标的路径不能替代。
