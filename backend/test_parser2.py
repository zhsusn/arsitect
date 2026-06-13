from app.services.ai_output_parser import AIOutputParser

output = """**根因分析**

C4 设计文档中将 "React 19 SPA" 定义为一个容器。

**修复策略说明**

采用方案 A。

```tsx
import React from 'react'

export const FrontendSpa = () => {
  return <div>frontend-spa</div>
}
```

**验证建议**
"""

changes = AIOutputParser.parse_file_changes(output, fallback_target="frontend/src/containers/frontend-spa/index.tsx")
print("changes:", changes)
for k, v in changes.items():
    print(f"--- {k} ---")
    print(repr(v))
