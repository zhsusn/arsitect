#!/usr/bin/env python3
fixes = [
    ('feature-04-gate-center/module-design.md', 'retry'),
    ('feature-16-pocketflow/module-design.md', 'PASSED'),
    ('feature-20-proto-arch/module-design.md', 'approve'),
]

for rel_path, keyword in fixes:
    path = f'openspec/changes/sdlc-visualizer/detailed-design/{rel_path}'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if keyword in content:
        print(f'OK: {rel_path} contains "{keyword}"')
    else:
        print(f'WARN: {rel_path} missing "{keyword}"')

path = 'openspec/changes/sdlc-visualizer/detailed-design/shared/db-schema.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'regeneration' in content:
    print('OK: db-schema.md contains regeneration')
else:
    print('WARN: db-schema.md missing regeneration')
