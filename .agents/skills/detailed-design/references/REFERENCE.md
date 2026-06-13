# Detailed Design 参考文件索引

本目录存放 `detailed-design` Skill 生成 module-design.md 各章节时按需加载的深度参考文件。

## 文件清单

| 文件名 | 加载时机 | 内容说明 |
|---|---|---|
| `backend-design-guide.md` | 生成第 1/2/3/5 章时 | 后端分层架构模板、类/函数设计规范、代码风格速查、OpenAPI 3.1 示例、DDL 模板、状态机规范、测试策略模板 |
| `frontend-design-guide.md` | 生成第 6 章时（必载） | 页面布局模式库（8 种标准布局）、设计反模式清单、a11y 检查表、响应式策略、动效策略、设计 Tokens 规范、空/加载/错误状态策略、组件架构对齐规范 |
| `page-spec-template.md` | 生成第 6.3 节时（必载） | PageSpec 标准表格模板（空白），含字段明细与 actions 明细子表格示例 |
| `mermaid-style-guide.md` | 生成任何 Mermaid 图表时 | 所有图表类型的工程规范（flowchart、sequenceDiagram、classDiagram、stateDiagram-v2、ER 图、页面拓扑图）与生成后检查清单 |

## 使用方式

Skill 主文件（`../SKILL.md`）的 Step 2 和 Step 3 中明确指定了各参考文件的加载规则。执行时按渐进式披露原则加载，禁止将参考文件内容直接复制到主文件正文。
