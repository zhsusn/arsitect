# PRD 的 c4_binding 生成指南

## system_id 派生规则
从项目名称自动转换为 kebab-case：
- "SDLC Visualizer" → "sdlc-visualizer"
- "供应链融资平台" → "supply-chain-financing"

## external_systems 提取规则
在 PRD 的"竞品格局"和"外部依赖"章节中，识别以下信号：
- "需对接 xxx 系统" → 外部系统
- "通过 xxx API 获取数据" → 外部系统
- "与 xxx 平台集成" → 外部系统

## actors 提取规则
在 PRD 的"用户画像"和"角色职责描述"章节中，识别以下信号：
- 每个 Persona 对应一个 Actor
- `role_type` 判定：核心业务操作者 → PRIMARY / 辅助角色 → SECONDARY / 系统/定时任务 → SYSTEM
