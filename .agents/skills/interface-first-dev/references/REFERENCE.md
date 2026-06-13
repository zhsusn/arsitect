# Interface-First Development 参考文档

## 本目录文件说明

| 文件 | 用途 | 加载时机 |
|------|------|----------|
| `output-checklist.md` | 输出前格式自检清单（YAML Front Matter、C4 标签、依赖完整性） | Step 9 质量检查前 |

## 文档规范要点

本 Skill 产出物遵循 DocForge 文档规范：

1. **接口契约 Markdown 文档**（`api-design.md`）头部必须包含标准 YAML Front Matter：
   - `doc_type: "API_DESIGN"`
   - `fragment_id: "api-{iteration}-{module-seq}"`
   - `c4_binding.level: "L3"`
   - `c4_binding.component_id` / `container_id` 指向上游文档

2. **@C4-Interface 标签**：每个接口章节首行必须插入 `@C4-Interface:{METHOD} {path}`

3. **OpenAPI 3.1**：`openapi.yaml` 作为机器消费格式，`api-design.md` 作为人类阅读 + C4 绑定载体

## 版本历史

- 2026-06-10: 增加 DocForge 文档规范支持（YAML Front Matter + C4 绑定）
