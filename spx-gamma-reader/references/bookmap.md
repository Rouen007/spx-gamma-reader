# Bookmap 查阅与读图

## 先认字段和设置

检查 instrument/合约、交易所、数据源与深度、图上时间/时区、回放/实时状态。模拟交易标签不证明作者真实成交。时间轴没有日期时，日期依赖原始消息与上下文，不能凭文件名认定。

| 字段 | 能观察什么 | 不可直接推出什么 |
|---|---|---|
| Heatmap | 当前与历史可见限价流动性，持续、迁移、变淡或消失 | 永久支撑阻力、参与者身份、操纵意图 |
| COB / DOM | 当前挂单深度；检查是否聚合多档 | 历史成交量、冰山总量、真实净仓 |
| SVP / CVP | 会话或可视窗口成交分布；核验重置范围 | 当前挂单厚度、未经定义的 value area |
| Volume dots | 配置范围内的成交；检查 total/delta 模式和聚合 | 每个球必是单笔纯市价单、固定颜色含义 |
| CVD | 买方主动成交减卖方主动成交的累计值 | 撤单数量、未成交挂单、未来方向 |
| 吸收插件 | 设置阈值内某价位短时成交提示 | 必然反转、天然等于冰山 |
| Stops & Icebergs | 插件与数据支持时的检测事件 | 任意三角图标都代表同一事件、总量等于可见挂单 |

确认设置后再解释颜色、大小与标注。VP/VPI/POT、LT-Diff、紫/绿三角若无法识别插件，不擅自当作 HIRO、净流入或冰山。Heatmap 调色/归一化变化不证明绝对挂单增强。

## 关键位附近的观察链

先定义价格带，再问“挂单怎么变、成交怎么发生、价格移了多少”。从连续片段辨认，单图只能给候选。

| 现象 | 候选解释 | 下一步确认与反例 |
|---|---|---|
| 主动卖成交持续，价格在下沿不再延伸 | 买方吸收候选 | 能否收回并回踩保持；承接耗尽后跌破则失效 |
| 主动买成交持续，价格在上沿推进有限 | 卖方吸收候选 | 失败上攻及反抽；若成交后站稳上方，不强做反转 |
| 后续主动成交减少，价格停滞 | 衰竭候选 | 不自动归为大单吸收，需要成交量/时段比较 |
| 亮带变弱或消失 | 流动性减少 | 对照成交/quotes delta/订单事件；静态图不能区分撤单与成交消耗 |
| 连续成交跨多个档，价格位移扩大 | 扫穿候选 | 留在外侧并回踩保持；快速收回可能是失败突破 |
| 同价位持续成交且可见数量补充 | 补单或隐藏量候选 | 插件来源和事件核验后才写检测，否则不宣称确定冰山 |
| 上下流动性稳定、价格反复往返 | 区间候选 | 边缘拒绝与中轴穿越；单帧两堵墙不能保证全天区间 |

吸收观察成交被承接，衰竭观察主动后续力量减弱。都需价格确认，也可能先暂停后继续原方向。

## CVD 使用

记录品种、累积起点、session/chart 范围、手动或计划重置、成交量过滤。设置未知时只描述单帧读数；不把两个不可比截图的绝对值相减。相同设置才比较斜率、阶段变化与价格位移。

负 CVD 配合价格不跌：卖方主动成交占优但位移受限，是承接候选，不证明某机构买入或确定底部。正 CVD 配合价格不涨使用对称解释。背离可能持续；等待收回、失败推进或接受外侧。

“CVD 一撤”这类口语要拆开：CVD 走势变了，还是挂单撤走？未有报价或订单事件，只能记录前者或未知。标准 CVD 与 Stops/Icebergs 子图累计线也不是同一统计量。

## 冰山与插件

可见大挂单不是隐藏总量。确认冰山需要插件名称、数据源能力、事件类型与时间；停止单事件也不能从大成交球自行识别。官方 SI On-Chart 文档说明 CME MBO 实时数据要求及 D/T/E 等事件；依据当前插件文档核验，不按图标外观猜事件。重置、聚合和数据差异会影响检测。

## 与结构和价格合用

GEX 是结构条件，HIRO 是期权流估算的对冲压力，CVD 是成交统计，COB 是未成交挂单；不能互相改名。价格在关键位的接受/拒绝决定候选是否确认。

结构下沿 + 卖方主动成交 + 下跌位移受限 → 承接候选；收回区间并回踩保持 → 价格确认。若关键位外侧接受、挂单消失且位移扩大，则旧假设失效；不要求解释为同一参与者转向。

SPX/ES 核对同刻配对报价后才换算，基差保留采样时间。只给 Bookmap 仍可分析，不强制补 GEX、HIRO 或 COR1M。

## 官方查阅顺序

遇到不明字段查最贴近字段的官方文档，记录查询时间。无法对应插件或版本时保持未知，不自动购买/启用插件或连接新订阅。

- [主图与 Heatmap](https://bookmap.com/knowledgebase/docs/KB-SettingUpAndOperating-HeatmapMainChart)：挂单与成交。
- [Columns](https://bookmap.com/knowledgebase/docs/KB-SettingUpAndOperating-Columns)：COB、成交分布、quotes delta、重置。
- [CVD](https://bookmap.com/knowledgebase/docs/KB-Indicators-CVD)：累计范围、过滤、重置。
- [Absorption](https://bookmap.com/knowledgebase/docs/KB-Indicators-Absorption)：阈值、气泡与 sweeps 的区别。
- [吸收与衰竭](https://bookmap.com/en/learning-center/supply-demand-setups/supply-demand-setups/absorption-exhaustion)：观察对象与确认。
- [Stops & Icebergs On-Chart](https://bookmap.com/knowledgebase/docs/Addons-Stops-And-Icebergs-On-Chart-Indicator)：数据能力、事件、检测限制。
- [Heatmap settings](https://bookmap.com/knowledgebase/docs/KB-SettingUpAndOperating-HeatmapSettings)：显示阈值与有限深度。

本次字段核对：2026-10-10。没有长期胜率结论。
