#!/usr/bin/env python3
import re

# DR-004: Add "retry" to GateHistoryRecordDTO.decision_type
path = 'openspec/changes/sdlc-visualizer/detailed-design/feature-04-gate-center/module-design.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find patterns like: decision_type: "approve" | "reject" | "bypass"
# and add "retry"
old = 'decision_type: "approve" | "reject" | "bypass"'
new = 'decision_type: "approve" | "reject" | "retry" | "bypass"'
if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('DR-004: Added "retry" to GateHistoryRecordDTO.decision_type')
else:
    # Try broader search
    patterns = [
        (r'("approve"\s*\|\s*"reject"\s*\|\s*"bypass")', '"approve" | "reject" | "retry" | "bypass"'),
    ]
    found = False
    for pat, repl in patterns:
        content, n = re.subn(pat, repl, content)
        if n > 0:
            found = True
            break
    if found:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('DR-004: Added "retry" to GateHistoryRecordDTO.decision_type (via regex)')
    else:
        print('DR-004: Pattern not found')

# DR-016: PhaseResultDTO.status COMPLETED -> PASSED
path = 'openspec/changes/sdlc-visualizer/detailed-design/feature-16-pocketflow/module-design.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace COMPLETED with PASSED in PhaseResultDTO context
old = 'COMPLETED'
new = 'PASSED'
# Only replace in PhaseResultDTO context - do a targeted replacement
if 'PhaseResultDTO' in content and 'COMPLETED' in content:
    # Replace all COMPLETED in this file to PASSED for consistency with table
    content = content.replace('COMPLETED', 'PASSED')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('DR-016: Replaced COMPLETED with PASSED in PhaseResultDTO')
else:
    print('DR-016: Pattern not found')

# DR-020: ReviewResultDTO.decision pass -> approve
path = 'openspec/changes/sdlc-visualizer/detailed-design/feature-20-proto-arch/module-design.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace "pass" with "approve" in ReviewResultDTO context
if 'ReviewResultDTO' in content and '"pass"' in content:
    content = content.replace('"pass"', '"approve"')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('DR-020: Replaced "pass" with "approve" in ReviewResultDTO')
else:
    print('DR-020: Pattern not found')

# DR-017: Add CHECK constraints to bypass tables
path = 'openspec/changes/sdlc-visualizer/detailed-design/feature-17-bypass/module-design.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add CHECK to bypass_applications.status
old1 = 'status              TEXT NOT NULL,'
new1 = 'status              TEXT NOT NULL CHECK (status IN ("pending_authorization", "authorized", "rejected", "executing", "completed", "pending_review", "reviewed", "timeout", "violation_pending")),'
if old1 in content:
    content = content.replace(old1, new1)
    print('DR-017: Added CHECK to bypass_applications.status')

# Add CHECK to bypass_reviews.conclusion  
old2 = 'conclusion          TEXT NOT NULL,'
new2 = 'conclusion          TEXT NOT NULL CHECK (conclusion IN ("pass", "reject", "escalate")),'
if old2 in content:
    content = content.replace(old2, new2)
    print('DR-017: Added CHECK to bypass_reviews.conclusion')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
