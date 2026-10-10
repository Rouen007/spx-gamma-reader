# Rouen SPX / Bookmap Reader

从 [HaoyangHan/spx-gamma-reader](https://github.com/HaoyangHan/spx-gamma-reader) fork 的个人定制研究工具。帮助 AI 按证据读取 SPX/ES 图表，不提供行情订阅、自动交易或已验证收益模型。

定制重点：Bookmap 查阅与字段识别、Tuna 方法的证据分层、SPX/ES 时间与基差核对、连续截图台账、个人仓位风险层。

## 使用

将两个 Skill 目录安装到你的 AI 工具技能目录。Codex 可在本地 checkout 创建软链（修改为实际路径）：

```sh
ln -s /absolute/path/spx-gamma-reader/spx-gamma-reader ~/.codex/skills/spx-gamma-reader
ln -s /absolute/path/spx-gamma-reader/spx-gamma-reader-with-memory ~/.codex/skills/spx-gamma-reader-with-memory
```

已有同名目录时先检查归属，不覆盖。软链直接读取仓库正本。

示例请求：

> 用 spx-gamma-reader 分析这两张 ESZ6 Bookmap 与 SPX Heatmap。先核对截图时间和基差，区分成交吸收、挂单撤走与 CVD 变化，列价格确认和失效条件。

> 只看这张 Bookmap：哪些确实可见，哪些仍是候选解释？不要从最亮墙直接给方向。

个人上下文可用 `spx-gamma-reader-with-memory`，并明确提供仓位的更新时间和完整期权腿。

## 本地证据台账

macOS / Linux、Python 3.10+，只用标准库，不请求网络：

```sh
python3 spx-gamma-reader/scripts/ledger.py check examples/observation.json
python3 spx-gamma-reader/scripts/ledger.py append examples/observation.json --ledger local-evidence/session.jsonl
python3 -m unittest discover -s tests
```

检查证据不得晚于决策时点、SPX/ES 基差引用、CVD 设置是否可比。JSONL 新增记录，不改旧判断。工具不验证图片真实性、计算信号或决定下单。

## 文件入口

- [基础 Skill](spx-gamma-reader/SKILL.md)：输入、合图、条件路径。
- [Bookmap 查阅](spx-gamma-reader/references/bookmap.md)：面板、吸收、撤单、扫穿、冰山、CVD、官方文档。
- [Tuna 方法边界](spx-gamma-reader/references/tuna-framework.md)：本人、群友与研究归纳的区分。
- [连续证据](spx-gamma-reader/references/evidence-ledger.md)：时序、字段与复盘。
- [训练](spx-gamma-reader/references/exercises.md)：反例与判断题。
- [个人层](spx-gamma-reader-with-memory/SKILL.md)：事件、持仓与用户纪律。
- [来源说明](PROVENANCE.md)：上游与定制范围。

真实群聊、截图、私人持仓、Token 与原始采集不入公共仓库。示例全为合成。没有回测结果，不能将案例当作策略优势。
