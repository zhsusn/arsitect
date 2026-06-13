# PRD 输出前格式自检清单

在将文档写入文件系统前，必须完成以下检查：

□ YAML Front Matter 检查
  - 文件首行是否为 `---`？
  - `doc_type` 是否为 "PRD"？
  - `fragment_id` 是否符合 `prd-{iteration}-{seq}` 格式？
  - `version` 是否为有效 SemVer（如 1.0.0）？
  - `status` 是否为 DRAFT/REVIEW/FROZEN 之一？
  - `c4_binding.level` 是否为 "L1"？
  - `c4_binding.system_id` 是否为有效 kebab-case？

□ 锚点ID 检查
  - 所有 `##` / `###` 标题是否包含 `{#sec-xxx}` 锚点？
  - 同文档内锚点ID是否有重复？
  - 锚点ID是否只含小写字母、数字、下划线？

□ C4 标签映射表检查
  - 文档末尾是否包含《C4 标签映射表》？
  - `c4_binding.actors` 中每个 actor，映射表中是否有对应记录？
  - `c4_binding.external_systems` 中每个系统，映射表中是否有对应记录？

□ 依赖声明检查
  - `dependencies` 中的上游文档 fragment_id 和 version 是否已填充？

检查通过后方可写入文件。任一检查项失败，标记为 🔴 阻塞，列出修复清单。
