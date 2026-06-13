# High-Level Design 输出前格式自检清单

□ YAML Front Matter
  - 首行 `---`，`doc_type` = "ARCH"
  - `fragment_id` 格式 `arch-{iteration}-{3位序号}`
  - `version` = "1.0.0"，`version_type` = "BASELINE"
  - `status` ∈ {DRAFT, REVIEW, FROZEN}
  - `c4_binding.level` = "L2"

□ 锚点ID
  - 所有 `##` / `###` 含 `{#sec-xxx}`
  - 只含小写、数字、下划线，无重复

□ C4 标签映射表
  - 文档末尾包含《C4 标签映射表》，每个 `container_id` 在映射表中有对应记录
  - `container_relations.source/target` 在 `containers` 中存在

□ 依赖
  - `dependencies` 已填充上游 fragment_id + version
