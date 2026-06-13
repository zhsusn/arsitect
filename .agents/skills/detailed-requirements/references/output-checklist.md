# Detailed Requirements 输出前格式自检清单

□ YAML Front Matter
  - `doc_type` = "PRD"
  - `fragment_id` = `prd-{iteration}-{module-seq}`（3位序号）
  - `version` = "1.0.0"，`version_type` = "BASELINE"
  - `status` ∈ {DRAFT, REVIEW, FROZEN}
  - `c4_binding.level` = "L1"

□ 锚点ID
  - 所有 `##` / `###` 含 `{#sec-xxx}`
  - 同文档内无重复

□ C4 标签映射表（可选）
  - 文档末尾包含《C4 标签映射表》，实体与状态机标签在映射表中有对应记录

□ 依赖
  - `dependencies` 已填充上游 PRD fragment_id + version
