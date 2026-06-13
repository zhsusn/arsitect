#!/usr/bin/env python3

# Fix 1: _design-index.md project_members/operation_logs归属
path = 'openspec/changes/sdlc-visualizer/detailed-design/_design-index.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old1 = '| `project_members` | DR-014 | **公共表**（待提取） | — | 项目成员角色（MVP 本地用户） |'
new1 = '| `project_members` | DR-014 | **模块独占** | — | 项目成员角色（MVP 本地用户，P1 多用户后再评估） |'
if old1 in content:
    content = content.replace(old1, new1)
    print('Fixed: project_members归属')

old2 = '| `operation_logs` | DR-014 | **公共表**（待提取） | — | 操作日志（只追加，不可变） |'
new2 = '| `operation_logs` | DR-014 | **模块独占** | — | 操作日志（只追加，不可变，P1 多用户后再评估） |'
if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed: operation_logs归属')

# Fix 2: rework_events写方统一 (in section 10)
old3 = '| `rework_events` | DR-013 | 模块独占 | DR-014 | 返工事件记录（热力图数据源） |'
new3 = '| `rework_events` | DR-013 | 模块独占（写方：DR-003/004/008事件触发） | DR-013/014 | 返工事件记录（热力图数据源） |'
if old3 in content:
    content = content.replace(old3, new3)
    print('Fixed: rework_events写方')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Fix 3: DR-001 Active -> Cancelled rule
path2 = 'openspec/changes/sdlc-visualizer/detailed-design/feature-01-project-dashboard/module-design.md'
with open(path2, 'r', encoding='utf-8') as f:
    content2 = f.read()

# The old rule: "直接阻断，提示先归档而非取消"
# New rule: "零执行时允许直接取消；已有执行记录时提示先归档"
old_rule = '| Active → Cancelled | 用户点击"取消项目" | 项目已处于 Active 态且已确认，影响面大 | 直接阻断，提示先归档而非取消 |'
new_rule = '| Active → Cancelled | 用户点击"取消项目" | 项目已处于 Active 态且已确认，影响面大 | **零执行**（无任何 Stage 被执行）时允许直接取消；已有执行记录时阻断，提示先归档（Active → Archived → Cancelled） |'
if old_rule in content2:
    content2 = content2.replace(old_rule, new_rule)
    with open(path2, 'w', encoding='utf-8') as f:
        f.write(content2)
    print('Fixed: DR-001 Active→Cancelled rule')
else:
    print('WARN: DR-001 rule pattern not found')
