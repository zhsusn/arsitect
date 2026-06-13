#!/usr/bin/env python3
import yaml
import json

with open('openspec/changes/sdlc-visualizer/interface-contracts/openapi.yaml', 'r', encoding='utf-8') as f:
    spec = yaml.safe_load(f)

print('=== OpenUI (DR-018) Endpoints ===')
for path, methods in spec['paths'].items():
    if 'openui' in path:
        for m, op in methods.items():
            print(f'  {m.upper():6s} {path:40s} {op["summary"]}')

print()
print('=== Wireframe (DR-019) Endpoints ===')
for path, methods in spec['paths'].items():
    if 'wireframe' in path:
        for m, op in methods.items():
            print(f'  {m.upper():6s} {path:40s} {op["summary"]}')

print()
print('=== Mock Data Coverage ===')
with open('openspec/changes/sdlc-visualizer/interface-contracts/mock-data.json', 'r', encoding='utf-8') as f:
    mock = json.load(f)

openui_ops = [k for k in mock if 'openui' in k.lower() or 'open' in k.lower()]
wireframe_ops = [k for k in mock if 'wireframe' in k.lower()]
print(f'OpenUI mock operations: {len(openui_ops)}')
for op in openui_ops:
    print(f'  - {op}')
print(f'Wireframe mock operations: {len(wireframe_ops)}')
for op in wireframe_ops:
    print(f'  - {op}')
