from app.services.ai_output_parser import AIOutputParser

# Simulate Windows CRLF output from Kimi CLI
output = "=== FILE: frontend/src/containers/frontend-spa/index.tsx ===\r\n\r\n```tsx\r\nimport React from 'react'\r\n\r\nexport const FrontendSpa = () => {\r\n  return <div>frontend-spa</div>\r\n}\r\n```\r\n\r\n**验证建议**\r\n"

changes = AIOutputParser.parse_file_changes(output, fallback_target="frontend/src/containers/frontend-spa/index.tsx")
print("changes:", changes)
for k, v in changes.items():
    print(f"--- {k} ---")
    print(repr(v))
