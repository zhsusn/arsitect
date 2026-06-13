#!/usr/bin/env python3
import glob
import re

files = sorted(glob.glob('openspec/changes/sdlc-visualizer/detailed-design/feature-*/module-design.md'))
print(f'Found {len(files)} module-design.md files')

fixed = 0

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    for i, line in enumerate(lines):
        # Only process first 15 lines (frontmatter area)
        if i >= 15:
            break
        # Match Chinese status lines with Draft/Active
        if '状态' in line and ('Draft' in line or 'Active' in line):
            original = line
            line = re.sub(r'Draft\s*→\s*Active', 'FROZEN', line)
            line = re.sub(r'Draft(?!\w)', 'FROZEN', line)
            line = re.sub(r'Active(?!\w)', 'FROZEN', line)
            if line != original:
                lines[i] = line
                modified = True
                break  # Only fix first occurrence
    
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        module = path.replace('\\', '/').split('/')[-2]
        print(f'  Updated status: {module}')
        fixed += 1

print(f'\nFixed status: {fixed}/{len(files)}')
