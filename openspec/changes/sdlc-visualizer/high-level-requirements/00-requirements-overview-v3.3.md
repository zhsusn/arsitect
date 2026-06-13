

---

# AI Code 研发平台 — 产品需求与架构设计文档（v3.3 完整版）

> **版本**: v3.3（双态模型优化版） **状态**: 正式基线 **日期**: 2026-05-30 **目标读者**: 产品负责人、技术负责人、架构师、项目经理、研发团队 **变更说明**: 引入 Draft/Active 双态模型，规模评估 Skill 输入明确为头脑风暴结果或概要需求，全文章节衔接对齐

---

## 目录

- [1. 引言](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#1-%E5%BC%95%E8%A8%80)
    
- [2. 核心概念与项目定义](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#2-%E6%A0%B8%E5%BF%83%E6%A6%82%E5%BF%B5%E4%B8%8E%E9%A1%B9%E7%9B%AE%E5%AE%9A%E4%B9%89)
    
- [3. 项目规模评估体系（Skill-SizeEstimate）](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#3-%E9%A1%B9%E7%9B%AE%E8%A7%84%E6%A8%A1%E8%AF%84%E4%BC%B0%E4%BD%93%E7%B3%BB)
    
- [4. 渐进式冻结与人工参与模型](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#4-%E6%B8%90%E8%BF%9B%E5%BC%8F%E5%86%BB%E7%BB%93%E4%B8%8E%E4%BA%BA%E5%B7%A5%E5%8F%82%E4%B8%8E%E6%A8%A1%E5%9E%8B)
    
- [5. Human-in-the-Loop（HITL）设计](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#5-human-in-the-loop-hitl-%E8%AE%BE%E8%AE%A1)
    
- [6. 功能需求](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#6-%E5%8A%9F%E8%83%BD%E9%9C%80%E6%B1%82)
    
- [7. 可观察性体系（Observability）](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#7-%E5%8F%AF%E8%A7%82%E5%AF%9F%E6%80%A7%E4%BD%93%E7%B3%BBobservability)
    
- [8. 架构设计](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#8-%E6%9E%B6%E6%9E%84%E8%AE%BE%E8%AE%A1)
    
- [9. 状态机与执行模型](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#9-%E7%8A%B6%E6%80%81%E6%9C%BA%E4%B8%8E%E6%89%A7%E8%A1%8C%E6%A8%A1%E5%9E%8B)
    
- [10. 数据架构](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#10-%E6%95%B0%E6%8D%AE%E6%9E%B6%E6%9E%84)
    
- [11. 安全设计](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#11-%E5%AE%89%E5%85%A8%E8%AE%BE%E8%AE%A1)
    
- [12. 角色与治理（RACI）](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#12-%E8%A7%92%E8%89%B2%E4%B8%8E%E6%B2%BB%E7%90%86raci)
    
- [13. 项目初始化契约](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#13-%E9%A1%B9%E7%9B%AE%E5%88%9D%E5%A7%8B%E5%8C%96%E5%A5%91%E7%BA%A6)
    
- [14. 演进路线与里程碑](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#14-%E6%BC%94%E8%BF%9B%E8%B7%AF%E7%BA%BF%E4%B8%8E%E9%87%8C%E7%A8%8B%E7%A2%91)
    
- [15. 待决策项定论](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#15-%E5%BE%85%E5%86%B3%E7%AD%96%E9%A1%B9%E5%AE%9A%E8%AE%BA)
    
- [16. 关键矛盾最终方案](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#16-%E5%85%B3%E9%94%AE%E7%9F%9B%E7%9B%BE%E6%9C%80%E7%BB%88%E6%96%B9%E6%A1%88)
    
- [17. 业界对比与定位](https://www.kimi.com/chat/19e7897b-90a2-87c5-8000-09adeff575ee?chat_enter_method=new_chat#17-%E4%B8%9A%E7%95%8C%E5%AF%B9%E6%AF%94%E4%B8%8E%E5%AE%9A%E4%BD%8D)
    

---

## 1. 引言

### 1.1 背景与目标

当前业界缺乏面向 AI 辅助研发的统一流程管理平台。多数团队采用"手搓 Prompt + 人工跟进"模式，导致：

- 产物散落、版本混乱、难以追溯
    
- 阶段依赖难表达、AI 产出缺少人工门禁
    
- 跨模块/跨团队协作依赖人肉沟通、进度黑盒
    

**核心目标**：将 AI 应用于软件开发全生命周期，尽量减少人工干预，但关键节点必须人工决策；开发进度、风险、资源使用情况实时可视化。

**演进路线**：

表格

|阶段|时间|核心能力|技术特征|
|:--|:--|:--|:--|
|**一期（MVP）**|当前|LLM + Skill 编排 + **Draft/Active 双态**|研发拆为可复用 Skill，流程引擎调度，AI 生成、人决策；支持预立项 Draft 态|
|**二期（P1）**|+2 周|应用级视图 + RBAC + HITL|增强可观察性、人工审批节点、权限控制|
|**三期（P2）**|+4 周|Agent + Skill 协作|Agent 自主调用 Skill，平台控权限与人 Gate|
|**四期（P3）**|+4 周|企业级多人协作 + MCP|团队审查流、MCP Server 标准化、PostgreSQL|

### 1.2 范围边界

表格

|包含|排除|
|:--|:--|
|全生命周期产物生成（需求→设计→编码→测试→上线→运维）|具体 Skill 的 Prompt 工程、模型微调|
|多场景模板适配（Web/后端/数据/移动端/AI 模型）|底层 LLM 基座选型与训练|
|模块级里程碑独立推进与跨模块契约依赖|具体业务代码实现|
|工件版本、基线化、变更传播与 Stale 重跑|外部 CI/CD 工具链的替代|
|实时看板、进度追踪、资源消耗统计|通用项目管理（如 Jira 的完整替代）|
|Human-in-the-Loop 人工审批节点|—|
|可观察性体系（Tracing/Metrics/Logs）|—|

---

## 2. 核心概念与项目定义

### 2.1 四层空间模型

表格

|层级|概念|定义|生命周期|管理边界|
|:--|:--|:--|:--|:--|
|**组织层**|Workspace|团队/部门的研发资源边界，含多个应用|长期|成员目录、权限基线、全局模板|
|**应用层**|Application|长期存在的产品或系统，有独立用户群体和技术栈|长期|历史迭代继承、技术栈锁定、模块清单|
|**项目层**|Project|应用的一次迭代/变更，有明确交付目标和截止日期|短期（1~8 周）|规模等级、流程模板、责任人矩阵（RACI）|
|**模块层**|Module|应用内的功能子域，可独立设计、独立交付|随项目生灭|独立里程碑状态、独立工件版本|

**关键规则**：

- 1 Project ↔ 1 Application；1 Application → N Project
    
- 禁止：1 Project 包含 N Application（破坏边界、回滚、责任）
    
- 跨应用协作：通过契约工件引用（如 OpenAPI 文档）实现，不纳入同一项目
    

### 2.2 项目与迭代关系

表格

|模式|说明|适用场景|
|:--|:--|:--|
|**单项目单迭代**|一次立项 = 一个 Project|常规需求迭代|
|**大项目拆多迭代**|大目标拆成连续 Project|大型重构、跨季度|
|**同应用多项目并行**|多 Project 并行、模块隔离|多团队并行开发不同模块|

**冲突解决**：同应用、同模块并行 → 基线化工件串行；同应用、不同模块 → 完全并行。

---

## 3. 项目规模评估体系（Skill-SizeEstimate）

### 3.1 Skill-SizeEstimate 设计

项目规模评估抽象为独立可复用 Skill，在 **Draft → Active** 转换中分两次执行：

- **类型**：分析类 Skill（无业务产物，输出评估报告）
    
- **触发时机**：
    
    - **Triage（初估）**：Draft 项目创建后，输入业务目标即自动执行
        
    - **Calibrate（精修）**：Draft 阶段预立项分析 Skill 完成后、进入 Active 契约签订前执行
        
- **输入**：自然语言需求描述 + 可选已知指标（Triage 无已知指标；Calibrate 带入 Draft 实际产出）
    
- **输出**：规模三档得分、置信度、推荐等级、校准条件
    

### 3.2 输入输出定义

**Triage 输入（Input）**：

表格

|字段|类型|必填|说明|
|:--|:--|:--|:--|
|`requirement_text`|string|是|自然语言需求描述（原始业务目标）|
|`known_module_count`|int|否|已知模块数（Triage 阶段通常为空）|
|`known_api_count`|int|否|已知接口数（Triage 阶段通常为空）|
|`known_page_count`|int|否|已知页面数（Triage 阶段通常为空）|
|`tech_complexity`|int (1-5)|否|技术复杂度（Triage 阶段通常为空）|
|`risk_level`|int (1-5)|否|风险等级（Triage 阶段通常为空）|

**Calibrate 输入（Input）**：

表格

|字段|类型|必填|说明|
|:--|:--|:--|:--|
|`brainstorm_result`|object|是|**头脑风暴结果**：包含用户场景、痛点假设、价值主张、初步模块拆分|
|`requirement_summary`|string|是|**概要需求**：Draft 阶段产出的结构化需求摘要|
|`known_module_count`|int|是|实际模块数（从头脑风暴结果中提取）|
|`known_api_count`|int|是|实际接口数（从概要需求中提取）|
|`known_page_count`|int|是|实际页面数（从概要需求中提取）|
|`tech_complexity`|int (1-5)|是|技术复杂度（经技术可行性评估后确定）|
|`risk_level`|int (1-5)|是|风险等级（经风险识别后确定）|

**输出（Output）**：

JSON

复制

```json
{
  "optimistic_score": 20,
  "expected_score": 28,
  "conservative_score": 35,
  "level": "M",
  "confidence": "Medium",
  "dimension_details": [
    {"name": "模块数", "value": 5, "conf": "High", "weight": "30%"},
    {"name": "接口数", "value": 12, "conf": "Medium", "weight": "20%"},
    {"name": "页面数", "value": 8, "conf": "Medium", "weight": "15%"},
    {"name": "技术复杂度", "value": 3, "conf": "High", "weight": "20%"},
    {"name": "风险等级", "value": 2, "conf": "High", "weight": "15%"}
  ],
  "suggestion": "建议 M 级，模块数减少 30% 可降级为 S"
}
```

### 3.3 解析维度与推断规则

表格

|维度|关键词/模式|推断规则|权重|
|:--|:--|:--|:--|
|**模块数**|用户系统、订单、支付、权限、内容管理|1 业务域 ≈ 1 模块；"等"上浮 20%|**30%**|
|**接口数**|对接、调用、API、同步、回调、推送|2 模块交互 ≈ 3-5 接口；开放平台 ×2|**20%**|
|**页面数**|后台、管理端、H5、小程序、大屏|每模块 1-3 页；报表/大屏 +2|**15%**|
|**技术复杂度**|微服务、高并发、AI、分布式|1 无 / 2 低 / 3 中 / 4 高 / 5 极高|**20%**|
|**风险等级**|支付、资金、隐私、医疗、监管|1 无 / 2 低 / 3 中 / 4 高 / 5 极高|**15%**|

### 3.4 计算公式

plain

复制

```plain
规模得分 = (模块数 × 30%)
         + (接口数 × 0.8 × 20%)      ← 系数从 0.5 调整为 0.8
         + (页面数 × 0.4 × 15%)      ← 系数从 0.3 调整为 0.4
         + (技术复杂度系数 × 20%)
         + (风险等级系数 × 15%)
```

> **v3.3 优化**：接口数权重系数从 0.5 提升至 0.8，页面数从 0.3 提升至 0.4。实际项目中单个接口和页面的工作量往往被低估，调整后的公式更贴近真实规模。

输出三档：乐观（下限）、预期（中值）、保守（上限）。定级规则：以保守得分定档，标注"精修可降级"。

### 3.5 规模分级与流程裁剪

表格

|规模|保守得分|典型描述|流程模板|里程碑组合|
|:--|:--|:--|:--|:--|
|**XS**|≤ 10|改按钮、改校验、调超时|极简|Clarify(合并)→Build→Release|
|**S**|11~22|内部小工具、数据导入、单模块后台|快速|Clarify→Align(合并)→Build→Verify→Release|
|**M**|23~40|订单模块、权限 CMS、3 个业务域|标准|Clarify→Align→Contract→Build→Verify→Release|
|**L**|41~70|核心链路重构、AI 平台多子系统|完整|Clarify→Align→Contract→Build→Verify→Release(+预研)|
|**XL**|> 70|新一代核心系统、中台改造|专项|拆为多个 M 级子项目|

### 3.6 两次评估机制（Triage → Calibrate）

规模评估不是单次动作，而是在 **Draft → Active** 转换中**由粗到精**的两次校准。

#### 3.6.1 初估（Triage）：Draft 阶段自动触发

表格

|属性|说明|
|:--|:--|
|**触发时机**|Draft 项目创建后，输入业务目标即自动执行|
|**输入**|纯自然语言需求描述（无已知指标）|
|**推断方式**|纯关键词模式匹配（见 3.3 维度推断规则）|
|**精度**|低（仅用于判断 Draft 是否值得继续）|
|**输出**|三档得分 + 推荐等级 + 置信度（通常为 Low/Medium）|
|**决策价值**|若保守得分 > 70（XL），平台建议拆分子需求再进入 Draft；若 ≤ 10（XS），提示可快速立项|

#### 3.6.2 精修（Calibrate）：Active 契约签订前触发

表格

|属性|说明|
|:--|:--|
|**触发时机**|Draft 阶段预立项分析 Skill 完成后、进入 Active 契约签订前|
|**输入**|**头脑风暴结果**或**概要需求**：实际模块清单、接口数、页面数、技术复杂度、风险等级|
|**推断方式**|用实际值替换初估推断值，重新计算公式（见 3.4）|
|**精度**|高（置信度通常为 Medium/High）|
|**输出**|精修三档得分 + 最终等级 + 校准说明|
|**决策价值**|驱动流程模板选择、里程碑裁剪、时间盒设定|

#### 3.6.3 校准触发点与可能结果

表格

|校准触发点|操作|可能结果|
|:--|:--|:--|
|脑暴产出模块清单|用实际模块数替换推断值|模块数比初估少 30% 可降级|
|技术可行性评估|明确复杂度系数|新技术栈可能升级|
|风险识别|明确风险等级|资金/隐私强制升一档|
|精修后最终等级|TL/PM 人工覆盖|允许 ±1 级调整（需 PO 会签）|

---

## 4. 渐进式冻结与人工参与模型

### 4.1 核心原则

**"越往后变更成本越高，但前期鼓励推翻；后期不是不要人，而是人的介入从日常陪伴转为关键决策。"**

表格

|阶段区间|变更策略|人工参与特征|平台机制|
|:--|:--|:--|:--|
|**预立项（Draft）**|鼓励推翻，可随时终止|高频日常陪伴：临时 PO 主导价值判断，临时 TL 评估可行性，AI 生成多版方案|脑暴纪要、竞品分析、ROI 测算、终止建议书|
|**立项后→详设前（Active Clarify/Align）**|允许自由变化，范围可调|高频但轻量：PO 确认范围，PM 组织评审|版本化管理需求文档，无冻结|
|**详设过程中（Contract 前半）**|变化需走轻量评审|中频收敛：TL 主导架构决策，SO 介入安全设计|自动标记受影响模块，提示重跑范围|
|**详设完成后（Contract 后半）**|原则上冻结，大需求下迭代|低频但关键：基线化触发 CCB 流程|Stale 传播 + 强制人工确认重跑范围|
|**编码测试（Build/Verify）**|严格冻结，仅缺陷修复|低频一票否决：代码审查 Gate、测试通过 Gate|变更自动拒绝，需走异常流程回退到 Contract|
|**上线阶段（Release）**|完全冻结，热修复独立|峰值决策：上线审批 Gate 多人会签|上线包锁定，任何变更必须回退到 Contract|

### 4.2 Gate 分布与人工负荷

表格

|规模|Gate 总数|前期 Gate|后期 Gate|人工负荷|说明|
|:--|:--|:--|:--|:--|:--|
|XS|1|0|1（上线）|前 0% / 后 100%|Draft 立项 Gate 已完成后，Active 仅保留上线 Gate|
|S|2|1（设计）|1（上线）|前 50% / 后 50%|立项在 Draft 完成，Active 从 Align/Contract 开始|
|M|3|2（需求、架构）|1（上线）|前 67% / 后 33%|立项在 Draft 完成|
|L|4|2（预研、架构）|2（测试、上线）|前 50% / 后 50%|立项在 Draft 完成|
|XL|子项目累加|子项目独立|项目群统筹|专职 PMO|每个子项目各自走 Draft → Active|

**关键规则**：立项 Gate 在 Draft 态完成，不计入 Active 态 Gate 总数。每个 Active Gate 必须有且只有一个最终负责人（Accountable），防止集体决策无人负责。上线审批为唯一会签 Gate（PO+PM+SO+SRE），SRE 最终拍板。

---

## 5. Human-in-the-Loop（HITL）设计

### 5.1 设计目标

参考 Dify Human Input Node 和 LangGraph interrupt() 机制，在关键决策点引入明确的人工审批节点，实现"AI 执行、人工把关"的协作模式。

### 5.2 HITL 节点分布

表格

|HITL 节点|触发时机|审批人|操作选项|超时处理|
|:--|:--|:--|:--|:--|
|**立项 Gate**|**Draft 阶段完成后**（预立项决策）|临时 PO|通过 / 驳回 / 补充需求|48h 提醒，72h 自动驳回|
|**范围确认 Gate**|Active Clarify 阶段完成后|PO|通过 / 驳回 / 需修改|24h 提醒，48h 自动驳回|
|**架构评审 Gate**|Contract 阶段完成后|TL|通过 / 驳回 / 需修改|24h 提醒，48h 自动驳回|
|**代码审查 Gate**|Build 阶段完成后|TL|通过 / 驳回 / 需修改|24h 提醒|
|**测试通过 Gate**|Verify 阶段完成后|QA|通过 / 驳回|24h 提醒|
|**上线审批 Gate**|Release 阶段|SRE（会签 PO+PM+SO）|通过 / 驳回 / 延期|12h 提醒，24h 自动驳回|

### 5.3 实现方案：Waiting 状态

在 Skill 状态机中引入 **Waiting** 状态：

plain

复制

```plain
Pending → Running → Success / Failed
                    ↓
                 Waiting（需人工确认）
                    ↓
              人工通过 → Success
              人工驳回 → Failed（可重试）
```

**行为定义**：

- Skill 执行完成但命中 HITL 节点时，状态变为 Waiting
    
- Waiting 状态下释放执行锁，不阻塞其他 Skill
    
- 人工审批结果通过 WebSocket 实时推送
    
- 超时未审批自动驳回，记录到审计日志
    

### 5.4 旁路审批机制

对于紧急情况，支持"先执行后补审"模式：

- 需 SO 或 TL 提前授权
    
- 执行过程全量记录
    
- 事后 24h 内必须补审批，否则触发告警
    

---

## 6. 功能需求

### 6.1 全生命周期产物生成

表格

|阶段|标准产物（M 级以上）|裁剪产物（S 级以下）|人工 Gate|
|:--|:--|:--|:--|
|**Draft（预立项）**|脑暴纪要、竞品分析、可行性评估、ROI 测算、规模初估报告|纪要 + 价值一句话 + 初估|立项 Go/No-Go（临时 PO 为 A）|
|**Active Clarify**|范围确认书、用户故事、验收标准（继承 Draft 脑暴纪要并精修）|需求设计一页纸 + 草图|范围确认（PO 为 A）|
|**Align**|PRD、Feature Spec、接口契约初稿|需求设计一页纸 + 草图|范围确认（PO 为 A）|
|**Contract**|HLD、DD、OpenAPI、DB 设计、安全设计|技术方案 + 关键接口|架构评审（TL 为 A）|
|**Build**|代码、单元测试、集成脚本、部署配置、日志规范|代码 + 单元测试|代码审查（TL 为 A）|
|**Verify**|测试报告、性能基准、安全扫描报告、兼容性报告|测试报告 + 核心链路通过|测试通过（QA 为 A）|
|**Release**|上线 Checklist、监控配置、回滚方案、值班表|Checklist + 回滚命令|上线审批（会签，SRE 为 A）|

### 6.2 多场景模板

表格

|场景模板|里程碑差异|典型产物|
|:--|:--|:--|
|**Web 应用**|增加前端兼容性测试 Phase|页面原型、前端组件、E2E 测试|
|**后端服务**|强调接口契约 + 性能压测|OpenAPI、单元测试、压测报告|
|**数据管道**|增加数据质量校验 Phase|血缘图、Schema 变更、数据对账|
|**移动端**|增加机型适配 + 包体积检测|安装包、热更新脚本、崩溃分析|
|**AI 模型**|增加训练数据审查 + 模型评估|数据集、模型文件、评估报告|

### 6.3 里程碑与变更管理

- **工件多版本草稿**：基线前任意修改；基线后变更触发 Stale 传播
    
- **时间盒（Timebox）**：里程碑硬截止，到期强制推进或裁剪
    
- **范围锚定（Scope Anchor）**：启动时锁定模块清单，新增模块需人工确认并重估
    
- **影响分析引擎**：自动计算变更传播范围；重跑/复用/终止由人工决策
    

### 6.4 并行与历史分析

表格

|分析维度|平台能力|
|:--|:--|
|**应用级**|全景视图：迭代状态、成功率、平均交付周期|
|**迭代级**|单次 Project 完整轨迹、阶段耗时、Gate 等待、重跑次数|
|**阶段级**|Skill 历史成功率、Token 消耗、常见失败模式|
|**瓶颈识别**|自动标记 Gate 长等待、频繁 Stale 重跑、超时模块|

---

## 7. 可观察性体系（Observability）

参考 LangGraph + LangSmith 设计，构建三位一体的可观察性体系。

### 7.1 Skill 执行 Tracing

表格

|追踪维度|记录内容|用途|
|:--|:--|:--|
|**执行链路**|每个 Skill 的输入/输出/中间状态|问题定位、审计追溯|
|**Token 消耗**|按 Project/Phase/Skill 统计 AI 调用成本|成本分析、预算控制|
|**耗时分析**|每个 Phase 的执行耗时、等待耗时|瓶颈识别、效率优化|
|**依赖图谱**|Skill 间的输入输出依赖关系|影响分析、优化并行|

### 7.2 Metrics 指标体系

表格

|指标类别|具体指标|采集方式|
|:--|:--|:--|
|**成功率**|Skill 成功率、Phase 成功率、Project 成功率|状态机事件|
|**质量指标**|代码审查通过率、测试通过率、安全扫描通过率|Gate 事件|
|**效率指标**|平均交付周期、Gate 等待时长、重跑次数|旁路追踪|
|**资源指标**|Token 消耗总量、API 调用次数、存储占用|执行日志|

> **统计口径**：Draft 态的 Token 消耗与执行耗时计入 **Application 级研发管理费**，不计入 Project 级资源指标；Active 态开始才纳入 Project 级统计。

### 7.3 失败模式分析

- 自动分类 Skill Failed 的原因模式（如：Prompt 质量问题、上下文不足、超时、依赖失败）
    
- 生成失败模式热力图，指导 Skill 优化
    
- 支持按模块/阶段/时间维度下钻分析
    

### 7.4 实时看板

- **项目看板**：Phase/Skill 状态实时更新（WebSocket 推送）
    
- **资源看板**：Token 消耗、API 调用实时监控
    
- **风险看板**：超时预警、失败告警、待审批提醒
    

---

## 8. 架构设计

### 8.1 六层概念模型

表格

|层级|概念|职责|
|:--|:--|:--|
|**组织层**|Workspace|团队边界、成员目录、权限基线|
|**应用层**|Application|产品定义、技术栈、历史迭代继承|
|**项目层**|Project|规模等级、流程模板、责任人矩阵（RACI）|
|**模块层**|Module|功能子域，独立里程碑推进|
|**阶段层**|Phase|里程碑状态（Clarify/Align/Contract/Build/Verify/Release）|
|**执行层**|Skill|AI 能力单元，产出工件；支持 HITL Waiting 状态|

### 8.2 微服务部署架构

plain

复制

```plain
接入层
├── 网关（认证/鉴权/限流/路由）
└── 前端（React 19 + Vite 6）

业务中台
├── 项目管理服务（Workspace/Application/Project/Module CRUD）
├── 流程编排服务（模板、里程碑、Gate、状态机、依赖调度）
├── 工件基线服务（版本、草稿/基线、变更、Stale 分析）
├── Skill 调度服务（注册、路由、并发、限流、重试、LLM 代理、HITL 控制）
├── 权限与 RACI 服务（角色、责任矩阵、审批流、RBAC）
├── 安全合规服务（扫描、密钥、隐私、审计）
├── 监控看板服务（进度、健康度、资源、瓶颈、Tracing）
└── HITL 服务（人工审批节点管理、通知、超时处理）

数据层
├── PostgreSQL（主数据）
├── Redis（缓存/锁/Session）
├── 对象存储（工件文件）
└── Elasticsearch（日志/审计/Tracing）

外部依赖
├── LLM 服务（Kimi CLI / 多 Provider）
├── Git 仓库
├── CI/CD 工具链
└── 监控系统
```

### 8.3 技术栈选型

表格

|层级|技术|版本|选型理由|
|:--|:--|:--|:--|
|前端框架|React|19|V1 升级路径明确，生态成熟|
|构建工具|Vite|6|零迁移成本，HMR 极速|
|画布组件|React Flow|12|原生 React 集成，支持分组/泳道|
|状态管理|Zustand|5|API 极简，TypeScript 友好|
|后端框架|FastAPI|0.115|异步原生，Pydantic 集成|
|ORM|SQLAlchemy|2.0|Mapped[] 类型注解，selectinload|
|**数据库**|**PostgreSQL**|**15+**|**MVP 后统一迁移，支持高并发**|
|WS 服务端|python-socketio|5|Room 模型成熟，协议兼容|
|数据校验|Pydantic|2|性能提升 5-50x|
|进程管理|asyncio + subprocess|标准库|统一 async 接口|
|可观察性|OpenTelemetry + Jaeger|—|分布式 Tracing 标准|

### 8.4 部署架构演进

表格

|阶段|部署模式|数据库|说明|
|:--|:--|:--|:--|
|**MVP**|单体双进程（前端静态 + Python）|SQLite|零运维，10 Project 上限|
|**P1**|单体多进程|PostgreSQL|迁移主数据库，引入连接池|
|**P2**|微服务拆分（Skill 调度独立）|PostgreSQL|Skill 调度拆为独立 Worker|
|**P3**|容器化（Docker/K8s）|PostgreSQL + Redis Cluster|企业级部署|

---

## 9. 状态机与执行模型

### 9.1 Skill 级状态机（增加 Waiting 状态）

plain

复制

```plain
[*] → Pending：Project 创建 / Skill 初始化
Pending → Running：系统触发执行（用户触发，非自动）
Running → Success：CLI 退出码 0 + 产物校验通过
Running → Failed：CLI 退出码非 0 / 超时 / 产物校验失败
Running → Waiting：命中 HITL 节点，需人工确认
Waiting → Success：人工审批通过
Waiting → Failed：人工审批驳回 / 超时自动驳回
Failed → Pending：用户手动重试
Success → [*]：Phase 继续 / 流程结束
```

### 9.2 Phase 级状态机（状态聚合）

plain

复制

```plain
[*] → Pending：Project 初始化
Pending → Running：首个 Skill 开始执行
Running → Success：全部 Skills Success
Running → Failed：任一 Skill Failed（非 Waiting）
Running → Waiting：全部 Skills 执行完毕且至少一个为 Waiting
Waiting → Success：所有 Waiting Skill 人工审批通过
Waiting → Failed：任一 Waiting Skill 人工审批驳回
Failed → Running：用户重试 Failed Skill 后
Success → [*]：进入下一 Phase / 流程结束
```

### 9.3 Project 级状态机（状态聚合）

plain

复制

```plain
[*] → Draft：用户发起创建（进入预立项态）
Draft → Created：立项 Go/No-Go 通过 + 流程模板确认 + Active 态所有正式责任人确认
Draft → Cancelled：立项驳回 / 超时 / 用户主动终止
Created → Running：用户触发执行
Running → Success：全部 Phases Success
Running → Failed：任一 Phase Failed
Failed → Running：用户重试后
Success → [*]：流程结束
```

**Draft 态行为定义**：

- Draft 项目仅允许执行预立项分析型 Skill（脑暴、竞品分析、规模初估），禁止 Build/Verify 等执行型 Skill
    
- Draft 项目 7 天无活动自动迁移至 Cancelled，产物保留供复盘
    
- Draft → Created 的迁移为**刚性事务**：需同时满足「立项 Gate 通过」「流程模板已选」「全部 Active 正式责任人电子确认」
    

### 9.4 并行调度模型

表格

|锁级别|范围|规则|
|:--|:--|:--|
|**模块级串行锁**|同一 Module 内|有依赖关系的 Skills 串行执行|
|**模块内 Skill 并行**|同一 Module 内|**无输入输出依赖的 Skills 并行执行（D-001）**|
|**跨模块无锁**|不同 Module|完全并行|
|**跨项目无锁**|不同 Project|完全并行|
|**工件基线锁**|基线化 Artifact|下游读取需等待基线完成|
|**HITL 等待锁**|Waiting 状态 Skill|不持有执行锁，不阻塞其他 Skill|

### 9.5 Checkpointer 状态持久化

参考 LangGraph PostgresSaver/RedisSaver 设计：

- **工作流暂停恢复**：任何步骤可暂停，重启后从断点继续
    
- **系统重启不丢失**：Skill 执行状态持久化到 PostgreSQL
    
- **分布式执行支持**：多 Worker 共享状态，支持水平扩展
    
- **状态快照**：定期自动快照，支持回滚到任意历史状态
    

---

## 10. 数据架构

### 10.1 核心实体关系

plain

复制

```plain
Workspace ||--o{ Application : contains
Application ||--o{ Project : contains
Application ||--o{ Module : defines
Project }o--|| FlowTemplate : uses
Project ||--o{ ModuleInstance : executes
ModuleInstance ||--o{ Phase : contains
Phase ||--o{ SkillExecution : contains
SkillExecution }o--|| SkillDefinition : uses
SkillExecution ||--o{ Artifact : produces
SkillExecution ||--o{ ExecutionLog : generates
SkillExecution ||--o{ HITLRecord : may_have
Project ||--o{ TracingSpan : generates
```

### 10.2 存储策略

表格

|数据类型|存储|策略|
|:--|:--|:--|
|业务实体|PostgreSQL|主从复制，连接池|
|模板版本|PostgreSQL|不可变插入，禁止 UPDATE 结构|
|执行日志|PostgreSQL + ES|按 SkillExecution 分区，ES 用于检索|
|产物文件|对象存储|按 projects/{project_id}/phases/{phase_id}/skills/{skill_id}/ 组织|
|状态快照|PostgreSQL（JSONB）|Checkpointer 持久化|
|Tracing 数据|Jaeger + ES|异步写入，保留 7 天|

---

## 11. 安全设计

### 11.1 安全嵌入阶段

表格

|安全维度|设计要求|责任人|嵌入阶段|
|:--|:--|:--|:--|
|**安全设计审查**|涉及用户数据/资金/权限模块，Contract 阶段输出威胁建模 + 数据流图|SO|Contract|
|**密钥与凭证管理**|禁止 AI 产物硬编码密钥；配置中心注入；提交前自动扫描敏感词|AIE + SO|Build|
|**代码安全扫描**|强制 SAST + 依赖漏洞扫描，高危漏洞阻塞 Verify Gate|SO + QA|Build/Verify|
|**数据隐私合规**|涉及 PII 必须显式声明，输出隐私影响评估（PIA）|SO + PO|Align|
|**上线前安全 Gate**|SO 对扫描结果、密钥管理、访问控制一票否决|SO|Release|

### 11.2 RBAC 权限模型（P1 阶段引入）

表格

|角色|模板管理|项目创建|项目执行|Skill 重试|产物查看|审批权限|
|:--|:--|:--|:--|:--|:--|:--|
|**模板设计者**|CRUD|是|是|是|是|—|
|**项目执行者**|仅查看|是|是|是|是|—|
|**审批者（PO/TL/QA/SO）**|—|—|查看|—|查看|对应 Gate|
|**管理员**|全部|全部|全部|全部|全部|全部|

### 11.3 公共设计

表格

|条目|说明|
|:--|:--|
|配置管理|环境配置与代码分离，支持配置中心动态推送|
|日志与可观测性|统一结构化日志、Trace ID 全链路、关键指标自动上报|
|容量与性能|设计阶段明确 QPS/RT 目标，测试阶段压测验证|
|容灾与回滚|设计阶段明确 RTO/RPO，上线前回滚方案必须可执行|
|多环境管理|支持 dev/test/staging/prod 四级，产物晋升机制|
|文档即代码|所有设计文档、API 文档、运维手册与代码同仓库管理|

---

## 12. 角色与治理（RACI）

### 12.1 角色定义

表格

|角色|职责|独立性|
|:--|:--|:--|
|**PO（产品负责人）**|定义需求价值、确认范围、验收产物、裁决需求变更|必须独立|
|**TL（技术负责人）**|技术选型、架构评审、代码审查、技术风险兜底|必须独立|
|**PM（项目经理）**|进度跟踪、资源协调、里程碑 Gate 组织、风险上报|必须独立|
|**AIE（AI 平台工程师）**|维护 Skill 质量、优化 Prompt、监控 AI 产出合格率、管理 Skill 版本|独立角色（D-005）|
|**SO（安全负责人）**|安全设计审查、密钥管理、合规审计、上线前安全 Gate|≥ M 强制指定（D-006）|
|**Dev（开发工程师）**|执行编码 Skill、修复 AI 产出缺陷、补充边界测试|执行层|
|**QA（测试工程师）**|设计测试策略、验收 AI 生成测试用例、执行探索性测试|执行层|
|**SRE（运维负责人）**|部署配置审查、监控配置、上线值守、回滚执行|执行层|

### 12.2 阶段-任务责任矩阵

表格

|阶段|关键任务|PO|TL|PM|AIE|SO|Dev|QA|SRE|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
|**Draft**|脑暴/竞品分析 Skill|A|C|I|R|I|I|I|I|
||立项 Go/No-Go Gate|A|C|R|I|C|I|I|I|
|**Active Clarify**|范围确认/需求精修|A|C|R|I|I|I|I|I|
|**Align**|需求生成 Skill|A|C|C|R|I|C|C|I|
||需求范围确认 Gate|A|C|R|I|I|I|I|I|
|**Contract**|概要设计 Skill|C|A|I|R|C|C|I|I|
||安全设计审查|C|C|I|I|A|C|I|I|
||架构评审 Gate|C|A|R|I|C|C|I|I|
|**Build**|代码生成 Skill|I|C|I|R|I|R/A|I|I|
||代码审查 Gate|I|A|I|I|I|R|C|I|
|**Verify**|集成测试执行|I|C|I|I|I|C|R/A|I|
||安全扫描|I|C|I|I|A|C|R|I|
||测试通过 Gate|C|C|R|I|C|C|A|I|
|**Release**|上线审批 Gate|A|C|A|I|A|I|I|R|

---

## 13. 项目初始化契约

项目创建不是"填表单"，而是一次**团队契约的签订**。但契约签订前，需求往往模糊、规模未知，因此引入**双态模型**：先进入 **Draft（预立项）** 做轻量澄清与规模初估，再基于清晰认知签订 **Active（正式执行）** 契约。

### 13.1 双态模型概述

表格

|维度|Draft 态（预立项）|Active 态（正式执行）|
|:--|:--|:--|
|**目标**|澄清需求、评估规模、判断立项价值|按确定流程交付产物|
|**流程模板**|仅绑定轻量预立项分析模板|按精修规模绑定完整流程（裁剪后）|
|**产物标准**|脑暴纪要、竞品分析、规模初估报告|按第 6 章标准产物清单执行|
|**Gate**|仅 1 个：立项 Go/No-Go（临时 PO 决策）|按规模配置三级 Gate|
|**RACI**|临时指定 PO/TL（可一人兼任）|完整矩阵，Gate 审批人必须独立|
|**Skill 调度**|仅允许预立项分析型 Skill|允许全阶段 Skill|
|**成本归属**|计入应用级研发管理费，不占用项目预算|计入项目预算，开始 Token 消耗统计|
|**超时处理**|7 天无活动自动归档为 Cancelled|按里程碑时间盒管理|
|**状态出口**|通过 → Active；驳回 → Cancelled|Success / Failed|

### 13.2 Draft 项目创建（预立项态）

#### 13.2.1 强制输出物

表格

|输出物|内容要求|责任人|平台机制|
|:--|:--|:--|:--|
|**脑暴纪要**|核心用户场景、痛点假设、价值主张|临时 PO|Skill-ClarifyBrainstorm 自动生成|
|**竞品分析**|3 款竞品对标、差异化机会|临时 PO|Skill-CompetitorAnalysis|
|**规模初估报告**|三档得分、推断依据、置信度、立项建议|AIE 辅助|Skill-SizeEstimate（Triage 模式）|
|**立项建议书**|Go/No-Go 理由、关键风险、退出条件|临时 PO|模板化问卷，AI 辅助生成|

#### 13.2.2 创建流程

plain

复制

```plain
用户发起创建
    │
    ▼
① 选择/创建 Application（确定技术栈、历史继承）
    │
    ▼
② 输入业务目标（自然语言需求描述）
    │
    ▼
③ 自动执行 Skill-SizeEstimate（Triage 初估）
    → 输出：规模区间 [乐观, 预期, 保守] + 推荐等级 + 置信度
    → 若保守得分 > 70（XL级），平台建议拆分子需求
    │
    ▼
④ 指定临时责任人：临时 PO（价值判断）+ 临时 TL（可行性评估）
    │
    ▼
⑤ 执行预立项分析 Skill（脑暴、竞品分析、ROI 测算）
    → 注：Draft 态仅允许分析型 Skill，禁止执行 Build/Verify 等交付型 Skill
    │
    ▼
⑥ 生成规模初估报告 + 立项建议书
    │
    ▼
⑦ 立项 Go/No-Go Gate（临时 PO 决策）
    → 通过：进入 Active 契约签订
    → 驳回：项目归档为 Cancelled，保留 Draft 产物供复盘
    → 补充需求：返回步骤⑤
```

#### 13.2.3 关键规则

- **Draft 不计入项目预算**：Token 消耗、执行耗时统计到 Application 级研发管理费，避免"立项即亏损"
    
- **7 天自动清理**：Draft 项目 7 天无活动（无 Skill 执行、无人工操作）自动归档为 Cancelled，防止僵尸项目
    
- **可自由推翻**：Draft 阶段可随时终止，不触发任何变更流程
    
- **仅分析型 Skill**：禁止执行 Build/Verify 等执行型 Skill，防止未立项即编码
    

### 13.3 Active 项目契约（正式执行态）

#### 13.3.1 强制输出物

表格

|输出物|内容要求|责任人|平台机制|
|:--|:--|:--|:--|
|**项目宪章**|目标、范围、成功标准、关键风险、退出条件|PM 牵头|基于 Draft 产物精修|
|**规模精修报告**|实际模块数、精修得分、最终等级、校准说明|AIE 辅助|Skill-SizeEstimate（Calibrate 模式）|
|**流程确认书**|规模等级、裁剪里程碑列表、时间盒|TL + PM|根据规模自动推荐，可人工覆盖|
|**责任矩阵（RACI）**|每个阶段的责任人、审批人、执行人|PM|从团队目录选择，Gate 审批人必须独立|
|**质量规约（DoD）**|每个阶段的出口标准|TL + QA|按规模加载默认模板|
|**变更控制制度**|变更审批路径、CCB 组成、终止条件|PM + TL|≥ M 强制启用 CCB|
|**沟通计划**|站会频率、评审会、风险上报路径|PM|默认模板|

#### 13.3.2 创建流程

plain

复制

```plain
Draft 立项 Gate 通过
    │
    ▼
① 精修规模评估（Calibrate）
    → 输入：Draft 阶段头脑风暴结果或概要需求
    → 用 Draft 实际产出（模块清单、接口数、页面数）替换初估推断值
    → 输出：最终规模等级 + 置信度 + 降级/升级建议
    │
    ▼
② 人工确认规模 + 选择/裁剪流程模板（TL/PM 可覆盖 AI 建议）
    │
    ▼
③ 锁定模块清单（Scope Anchor）：强制模块 + 可选模块
    │
    ▼
④ 指定完整责任人（RACI 终填）：Gate 审批人必须独立，不可兼任
    │
    ▼
⑤ 生成项目契约文档 + 团队电子确认
    → 项目宪章、规模精修报告、流程确认书、RACI、DoD、变更制度
    │
    ▼
⑥ 所有责任人确认后，项目状态变为 Active，进入 Clarify 阶段
    → Draft 产物（脑暴纪要、竞品分析）自动继承为 Active Clarify 阶段初稿
```

#### 13.3.3 关键规则

- **步骤⑥ 为刚性门禁**：所有责任人未确认前，项目处于"待启动"状态，不允许任何执行型 Skill 运行
    
- **规模可覆盖**：AI 推荐等级后，TL 有权上调一级（风险预留）或 PM 有权下调一级（需 PO 会签）
    
- **模块清单锁定**：Scope Anchor 一旦确认，新增模块需走变更流程（见第 6.3 节）
    
- **Draft 产物继承**：Active 的 Clarify 阶段可直接引用 Draft 脑暴纪要，避免重复工作；若 Draft 未做可行性评估，Active Clarify 阶段需补充
    

---

## 14. 演进路线与里程碑

### 14.1 MVP 阶段（4 周）

**目标**：核心执行闭环可用，含 Draft/Active 双态

表格

|周次|交付内容|验收标准|
|:--|:--|:--|
|W1|数据层 + 模板管理后端 + Skill-SizeEstimate（Triage 模式）|PostgreSQL Schema 完成（含 Draft/Active 双态、HITL/Tracing 预留字段），Template API CRUD 通过测试|
|W2|Draft 项目创建 + Skill 执行引擎（含 Waiting 状态预留）|创建 Draft 自动初始化队列，预立项分析 Skill 按序执行；禁止执行型 Skill 在 Draft 态运行|
|W3|Active 项目契约 + 流程画布 + 详情面板 + WS 事件 + HITL UI|动态画布渲染，实时状态同步，详情面板展示日志/产物；Draft → Active 迁移刚性事务通过测试|
|W4|产物浏览 + RBAC 基础 + 集成测试|产物预览正常，角色权限框架就位，E2E 测试通过（含 Draft 7 天自动清理）|

### 14.2 P1 阶段（2 周）

**目标**：应用级视图 + HITL 完整 + RBAC + 可观察性基础

表格

|周次|交付内容|验收标准|
|:--|:--|:--|
|W5|Application 聚合视图 + HITL 完整实现（含 Draft 立项 Gate）|审批流可配置，通知/超时/旁路机制可用；Draft 立项 Gate 独立计时|
|W6|RBAC 权限控制 + 可观察性基础（Tracing，区分 Draft/Active 统计口径）|角色权限生效，执行链路可追踪；Draft Token 不计入 Project 统计|

### 14.3 P2 阶段（4 周）

**目标**：Agent 化 + Checkpointer + 高级可观察性

表格

|周次|交付内容|验收标准|
|:--|:--|:--|
|W7-W8|协调者 Agent + 专家 Agent 框架|Agent 可自主分解任务、调度 Skill|
|W9|Checkpointer 状态持久化|工作流可暂停恢复，系统重启不丢失状态|
|W10|可观察性完善（Metrics/Logs/看板）|实时看板、失败模式分析可用|

### 14.4 P3 阶段（4 周）

**目标**：企业级多人协作 + MCP + 分布式

表格

|周次|交付内容|验收标准|
|:--|:--|:--|
|W11-W12|团队审查流 + 评论批注 + MCP Server|多人协作可用，Skill 工具调用标准化|
|W13-W14|PostgreSQL 性能优化 + 分布式执行|支持 50+ 并发 Active Project|

---

## 15. 待决策项定论

表格

|编号|问题|定论|说明|
|:--|:--|:--|:--|
|D-001|同一模块内 Skills 是否允许并行？|**允许**|无输入输出依赖的 Skills 可并行，有依赖的串行|
|D-002|Gate 是否支持"有条件通过"？|**暂不支持**|仅通过/驳回，复杂场景拆分为"驳回→修改→重新提交"|
|D-003|跨应用依赖是否在第一期实现？|**先不考虑**|第一期仅单应用内模块依赖，跨应用靠人工契约|
|D-004|历史数据分析内置还是导出 BI？|**第一期不做**|第一期仅支持实时看板，历史分析后续迭代|
|D-005|AI 平台工程师是否独立角色？|**独立角色**|不与 TL 兼任，确保 Skill 质量中立性|
|D-006|安全负责人是否强制指定？|**规模 ≥ M 强制指定**|XS/S 可由 TL 兼任但需安全认证|
|D-007|是否引入 HITL Waiting 状态？|**引入**|在关键 Gate 处支持人工审批暂停|
|D-008|是否采用 Checkpointer 持久化？|**P2 引入**|支持工作流暂停恢复和分布式执行|
|D-009|是否支持 MCP 标准化？|**P3 引入**|Skill 工具调用采用 MCP Server 形式|

---

## 16. 关键矛盾最终方案

表格

|矛盾|采纳方案|一句话理由|
|:--|:--|:--|
|项目级串行 vs 模块级并行|**模块级并行**|项目级串行会导致关键路径过长、资源闲置|
|无变更传播 vs Stale 影响分析|**Stale 机制**|没有自动化影响分析，无法支持"仅重跑受影响模块"|
|无 Gate vs 强制 Gate|**三级 Gate（按规模配置化）**|AI 不能替人签字，但 XS/S 可简化 Gate 密度|
|固定完成率 vs 动态时间盒|**里程碑时间盒 + 模块健康度**|节点动态发现，固定百分比必然失真|
|可视化工具 vs 编排引擎|**编排引擎为骨架，可视化为血肉**|缺少变更传播和依赖管理的"可视化"只是看板|
|完全串行 vs Phase 内并行|**Phase 内无依赖 Skill 并行**|无依赖的 Skills（如接口文档+单元测试）本可并行|
|SQLite vs PostgreSQL|**MVP 用 SQLite，P1 迁移 PostgreSQL**|MVP 快速验证，P1 起支撑企业级并发|
|无 RBAC vs 完整 RBAC|**MVP 简化，P1 引入完整 RBAC**|MVP 单用户场景简化，P1 起支持团队协作|
|创建即定流程 vs 规模后定流程|**Draft 预立项后定流程**|规模未知时定流程必然失真，先澄清再契约|

---

## 17. 业界对比与定位

### 17.1 对比矩阵

表格

|维度|本方案|Scrum/敏捷|SAFe|大厂规范|GitLab Flow|传统瀑布|
|:--|:--|:--|:--|:--|:--|:--|
|迭代单位|Project（变更级，1~8 周）|Sprint（2 周）|ART（季度）|需求/项目|MR 级|项目级（数月）|
|需求冻结|渐进式冻结（详设后基线化）|Sprint 内冻结|PI 后冻结|提测前冻结|MR 前冻结|需求阶段完全冻结|
|人工 Gate|三级 Gate + HITL Waiting + Draft 立项|Sprint Review|PI 评审|技术+发布评审|Code Review|阶段评审会|
|模块并行|模块级独立里程碑|团队级 Sprint|团队级迭代|按域拆分项目|分支级并行|阶段内部分并行|
|变更控制|Stale 传播 + CCB|Sprint 内拒绝|变更请求|变更评审|Revert MR|CCB|
|AI 集成|原生编排 AI Skill + Agent|无|无|Copilot 辅助|无|无|
|HITL 支持|内置 Waiting 状态 + 审批流 + Draft 立项|无|无|无|Code Review|无|
|可观察性|Tracing + Metrics + Logs|有限|有限|成熟|CI/CD 指标|有限|

### 17.2 一句话定位

**"用瀑布的骨架管里程碑，用敏捷的血肉管模块，用 AI 的自动化管执行，用人工 Gate 管决策，用可观察性管质量。"**

### 17.3 相比竞品优势

- **相比 Scrum**：解决了 Sprint 内冻结过早/过晚的矛盾，前期更敏捷，后期更可控
    
- **相比 SAFe**：避免了 ART 火车式的全员同步开销，模块级异步让不同团队按自己节奏推进
    
- **相比 Copilot**：将"辅助编码"升级为"全流程自动化生成 + HITL 人工决策"
    
- **相比 GitLab Flow**：从代码级持续集成上升到业务级持续交付，覆盖需求/设计/测试/上线
    
- **相比传统瀑布**：保留里程碑清晰边界，但允许模块级并行和前期自由变更
    

---

> **文档结束。** 本文档为 v3.3 完整版，引入 Draft/Active 双态模型，规模评估 Skill 输入明确为头脑风暴结果或概要需求，全文章节衔接对齐。



借鉴哪些开源项目

| 阶段     | 开源项目                          | 借鉴能力                                                                                   | 借鉴方式                             | 落地场景                                                                              |
| :----- | :---------------------------- | :------------------------------------------------------------------------------------- | :------------------------------- | :-------------------------------------------------------------------------------- |
| **需求** | **Coco Workflow**             | 自适应复杂度路由（Trivial / Light / Standard / Deep 信号检测与路径决策）                                  | 借鉴架构，零代码引入，自研 `ComplexityRouter` | 需求规模评估与执行路径分流：单文件 bug 走 hotfix，新微服务走完整流水线                                         |
| **需求** | **Dify**                      | Human Input Node / `interrupt()` 机制                                                    | 借鉴设计                             | 需求确认 Gate（Gate 1）等 HITL 人工审批节点，实现"AI 执行→人工确认→AI 再执行"                              |
| **设计** | **C4 InterFlow**              | Architecture as Code（YAML/JSON DSL 定义架构、代码反向生成、CLI 批量渲染、JSONPath-like 架构查询、CI/CD 原生集成） | **融合 DSL** + 依赖 CLI 工具调用         | 架构设计唯一真相源、架构漂移检测（设计 vs 代码反向生成对比）、GitHub Actions 自动出图                              |
| **设计** | **AI Wireframe Generator**    | LangGraph 多 Agent 流水线编排模式（需求解析→布局规划→SVG 渲染）                                            | 借鉴模式，自研领域节点                      | 领域感知线框引擎：`DomainMapper`→`LayoutPlanner`→`NavigationLinker`，将 C4 Container 自动映射到页面 |
| **设计** | **OpenUI** (WandB)            | 自然语言 → 多框架前端代码（React/Vue/Svelte）→ 实时预览                                                 | 依赖 Docker 服务，HTTP API 调用         | 高保真原型渲染后端，输入页面规范 + 接口契约，输出可交互 HTML 原型                                             |
| **设计** | **Structurizr**               | C4 DSL 标准语法与模型定义                                                                       | 兼容子集                             | C4 架构模型解析、序列化，与 `arsitect.aac.yml` 格式对齐                                           |
| **设计** | **React Flow**                | 流程画布可视化组件（分组/泳道/动态布局）                                                                  | 依赖库                              | 前端流程编排画布，展示 Phase/Skill 执行状态与 Gate 节点                                             |
| **编码** | **OpenHands** (原 OpenDevin)   | CodeAct 架构（Bash/Python/Browser 统一动作空间）+ Docker 沙箱自主执行                                  | 依赖 Docker 服务，REST API 调用         | L5 全自动沙箱执行器：无人值守代码生成、架构验证（生成后反向扫描对比 C4 设计）、夜间批处理                                  |
| **编码** | **PocketFlow** (GTPlanner 内核) | Node-Flow 抽象 + 三阶段生命周期（prep→exec→post）+ StageGate 状态机                                  | 借鉴架构，自研扩展                        | 平台级 Skill 调度引擎 `PocketFlowSkillExecutor`：统一封装 CLI 子进程、C4 上下文注入、SSE 实时推送           |
| **编码** | **LangGraph**                 | Checkpointer 状态持久化（`PostgresSaver`/`RedisSaver`）+ 状态机设计                                | 借鉴机制                             | 工作流暂停恢复、系统重启不丢失、多 Worker 分布式执行共享状态                                                |
| **编码** | **LangSmith**                 | 可观察性体系（Tracing / Metrics / Logs）                                                       | 借鉴设计                             | Skill 执行链路追踪、Token 消耗统计、失败模式自动分类与热力图                                              |
| **编码** | **markdown-it-py**            | Markdown 解析引擎 + 自定义插件扩展                                                                | 依赖库                              | 研发文档锚点提取、章节树构建、YAML Front Matter 与 `@C4-` 标签提取                                    |



