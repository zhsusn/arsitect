from app.services.ai_output_parser import AIOutputParser

output = """**根因分析**

C4 设计文档中将 "React 19 SPA" 定义为一个容器。

**修复策略说明**

采用方案 A。

=== FILE: frontend/src/containers/frontend-spa/index.tsx ===
```tsx
import React from 'react'

export interface FrontendSpaProps {
  // TODO: define props
}

export const FrontendSpa: React.FC<FrontendSpaProps> = () => {
  return <div>frontend-spa</div>
}

export default FrontendSpa
```

**验证建议**
1. 重新运行 C4 架构治理检查
"""

changes = AIOutputParser.parse_file_changes(output, fallback_target="frontend/src/containers/frontend-spa/index.tsx")
print("changes:", changes)
print("keys:", list(changes.keys()))
for k, v in changes.items():
    print(f"--- {k} ---")
    print(repr(v[:200]))
