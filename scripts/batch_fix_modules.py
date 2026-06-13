#!/usr/bin/env python3
import glob
import re

files = sorted(glob.glob('openspec/changes/sdlc-visualizer/detailed-design/feature-*/module-design.md'))
print(f'Found {len(files)} module-design.md files')

fixed_titles = 0
fixed_status = 0

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Fix 1: Replace section 5 title variations
    patterns = [
        (r'^## 5\.\s*测试策略', '## 5. 边界条件与异常处理'),
        (r'^## 5\s+测试策略', '## 5. 边界条件与异常处理'),
        (r'^# 5\.\s*测试策略', '# 5. 边界条件与异常处理'),
    ]
    for pat, repl in patterns:
        content, n = re.subn(pat, repl, content, flags=re.MULTILINE)
        if n > 0:
            fixed_titles += 1
            break
    
    # Fix 2: Replace Frontmatter status
    status_patterns = [
        (r'^status:\s*Draft\s*→\s*Active', 'status: FROZEN'),
        (r'^status:\s*Draft', 'status: FROZEN'),
        (r'^status:\s*Active', 'status: FROZEN'),
    ]
    for pat, repl in status_patterns:
        content, n = re.subn(pat, repl, content, flags=re.MULTILINE)
        if n > 0:
            fixed_status += 1
            break
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  Updated: {path.split("/")[-2]}')

print(f'\nFixed section 5 titles: {fixed_titles}/{len(files)}')
print(f'Fixed Frontmatter status: {fixed_status}/{len(files)}')
