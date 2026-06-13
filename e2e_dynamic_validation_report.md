# E2E Dynamic Validation Report

Generated: 34958.171

## Probe Matrix

| Probe | ID | Description | Status | Duration |
|-------|----|-------------|--------|----------|
| Baseline | B1 | All routes load cleanly | PASS | 33859ms |
| Baseline | B2 | Sidebar navigation changes URL | PASS | 10297ms |
| Baseline | B3 | Project selector persistence | PASS | 3031ms |
| Baseline | B4 | Backend health check | PASS | 313ms |
| Edge | E1 | Direct URL with projectId | PASS | 1687ms |
| Edge | E2 | ArchGovernance no-project fallback | PASS | 2360ms |
| Edge | E3 | Sidebar collapse/expand | PASS | 5140ms |
| Fault | F1 | Backend 500 graceful degradation | PASS | 5313ms |
| Fault | F2 | Slow network resilience | PASS | 11922ms |
| Drift | D1 | Repeat navigation consistency | PASS | 4375ms |
| Drift | D2 | Refresh preserves project selection | PASS | 4797ms |
| Drift | D3 | Round-trip state consistency | PASS | 4515ms |

## Summary

- **Passed**: 12
- **Failed**: 0
- **Total**: 12

**All probes passed.**

## Failure Details

