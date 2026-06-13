# Interface-First Dev 输出前格式自检清单

□ YAML Front Matter（api-design.md）
  - `doc_type` = "API_DESIGN"
  - `fragment_id` = `api-{iteration}-{module-seq}`（3位序号）
  - `version` = "1.0.0"，`version_type` = "BASELINE"
  - `status` ∈ {DRAFT, REVIEW, FROZEN}
  - `c4_binding.level` = "L3"

□ C4 标签映射表
  - 文档末尾包含《C4 标签映射表》，每个接口在映射表中有对应记录
  - `c4_binding.interfaces` 与 openapi.yaml paths 一一对应

□ 组件归属
  - `c4_binding.component_id` 在上游 DETAIL_DESIGN 中存在
  - `c4_binding.container_id` 在上游 ARCH 中存在

□ 依赖
  - `dependencies` 已填充上游 DETAIL_DESIGN 的 fragment_id + version
