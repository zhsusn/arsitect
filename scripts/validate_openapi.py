#!/usr/bin/env python3
import yaml
import re

def main():
    with open('openspec/changes/sdlc-visualizer/interface-contracts/openapi.yaml', 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    schemas = set(spec.get('components', {}).get('schemas', {}).keys())
    paths = spec.get('paths', {})

    # Check 1: duplicate operationId
    op_ids = []
    for path, methods in paths.items():
        for method, op in methods.items():
            if 'operationId' in op:
                op_ids.append(op['operationId'])

    duplicates = [oid for oid in op_ids if op_ids.count(oid) > 1]
    print('=== Check 1: Duplicate operationId ===')
    print(f'Total endpoints: {len(op_ids)}')
    if duplicates:
        print(f'FAIL: Duplicates found: {set(duplicates)}')
    else:
        print('PASS: No duplicate operationId')

    # Check 2: $ref validity
    with open('openspec/changes/sdlc-visualizer/interface-contracts/openapi.yaml', 'r', encoding='utf-8') as f:
        yaml_text = f.read()
    refs = set(re.findall(r'\$ref: [\"\']?#/components/schemas/([A-Za-z0-9_]+)[\"\']?', yaml_text))
    print('\n=== Check 2: $ref validity ===')
    print(f'Total unique schema refs: {len(refs)}')
    missing = refs - schemas
    if missing:
        print(f'FAIL: Missing schemas: {missing}')
    else:
        print('PASS: All $ref schemas exist')

    # Check 3: paginated GET endpoints have page params
    print('\n=== Check 3: Pagination params ===')
    get_endpoints = [(p, op) for p, methods in paths.items() for m, op in methods.items() if m == 'get']
    page_issues = []
    for path, op in get_endpoints:
        params = [pp.get('name') for pp in op.get('parameters', [])]
        resp200 = op.get('responses', {}).get('200', {})
        content = resp200.get('content', {})
        is_paginated = 'PageResponse' in str(content)
        if is_paginated and 'page' not in params:
            page_issues.append(path)

    if page_issues:
        print(f'WARN: GET endpoints missing page param: {page_issues}')
    else:
        print('PASS: All paginated GET endpoints have page params')

    # Check 4: Problem reference in error responses
    print('\n=== Check 4: Problem error responses ===')
    problem_issues = []
    for path, methods in paths.items():
        for method, op in methods.items():
            for code, resp in op.get('responses', {}).items():
                if code.startswith(('4', '5')):
                    content = resp.get('content', {})
                    if content and 'Problem' not in str(content):
                        problem_issues.append(f'{method.upper()} {path} {code}')
    if problem_issues:
        print(f'WARN: Error responses without Problem schema ({len(problem_issues)}):')
        for issue in problem_issues[:10]:
            print(f'  - {issue}')
    else:
        print('PASS: All error responses reference Problem')

    print('\n=== Summary ===')
    print(f'Schemas defined: {len(schemas)}')
    print(f'Paths defined: {len(paths)}')
    print(f'Operations defined: {len(op_ids)}')

if __name__ == '__main__':
    main()
