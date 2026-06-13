# Detailed Design 输出前格式自检清单

□ YAML Front Matter
  - `doc_type` = "DETAIL_DESIGN"
  - `fragment_id` = `detail-{iteration}-{module-seq}`（3位序号）
  - `version` = "1.0.0"，`version_type` = "BASELINE"
  - `status` ∈ {DRAFT, REVIEW, FROZEN}
  - `c4_binding.level` = "L3"

□ 容器映射
  - `c4_binding.container_id` 在上游 ARCH 的 `containers` 中存在
  - 不存在则标记 `[ASSUMPTION]`

□ C4 标签映射表
  - 文档末尾包含《C4 标签映射表》，每个 `component_id` 在映射表中有对应记录

□ 锚点ID
  - 所有 `##` / `###` 含 `{#sec-xxx}`，同文档内无重复

□ 依赖
  - `dependencies` 已填充上游 ARCH 和 PRD 的 fragment_id + version
