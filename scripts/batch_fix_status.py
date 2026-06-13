#!/usr/bin/env python3
import glob
import re

files = sorted(glob.glob('openspec/changes/sdlc-visualizer/detailed-design/feature-*/module-design.md'))
print(f'Found {len(files)} module-design.md files')

fixed = 0

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Match various "status: Draft" patterns in Chinese frontmatter
    patterns = [
        (r'\*\*状态\*\*\s*[:：]\s*Draft\s*→\s*Active', '**状态**：FROZEN'),
        (r'\*\*状态\*\*\s*[:：]\s*Draft', '**状态**：FROZEN'),
        (r'\*\*状态\*\*\s*[:：]\s*Active', '**状态**：FROZEN'),
        (r'状态\s*[:：]\s*Draft\s*→\s*Active', '状态：FROZEN'),
        (r'状态\s*[:：]\s*Draft', '状态：FROZEN'),
        (r'状态\s*[:：]\s*Active', '状态：FROZEN'),
    ]
    for pat, repl in patterns:
        content, n = re.subn(pat, repl, content)
        if n > 0:
            fixed += 1
            break
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        module = path.replace('\\', '/').split('/')[-2]
        print(f'  Updated status: {module}')

print(f'\nFixed status: {fixed}/{len(files)}')
