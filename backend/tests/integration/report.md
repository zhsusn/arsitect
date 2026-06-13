# Integration Test Report

> Generated: 2026-06-04
> Policy: default
> Strategy: default (敏捷/内部项目)

## Summary

| Metric | Value |
|--------|-------|
| Total Integration Tests | 16 passed |
| Total Suite | 540 passed, 4 skipped |
| Coverage | **92.79%** |
| Status | PASS |

## Test Files

| File | Tests | Status |
|------|-------|--------|
| test_health.py | 3 | PASS |
| test_sync1_baseline.py | 1 | PASS |
| test_sync2_execution.py | 1 | PASS |
| test_sync3_advanced.py | 1 | PASS |
| test_sync4_binding.py | 3 | PASS |
| test_sync5_bypass.py | 4 | PASS |
| test_sync6_openui.py | 3 | PASS |
| test_sync7_sketch.py | 3 | PASS |
| test_sync8_wireframe.py | 3 | PASS |
| test_upload.py | 2 | SKIP |

## P0 User Story Coverage

| User Story | Test IDs | Status |
|------------|----------|--------|
| US-003 Bypass Approval | TEST-1504 ~ TEST-1507 | PASS |
| US-015 OpenUI Prototype | TEST-1508 ~ TEST-1510 | PASS |
| US-016 Sketch/Wireframe | TEST-1511 ~ TEST-1516 | PASS |
| Binding Rule Management | TEST-1501 ~ TEST-1503 | PASS |

## Green Mirage Audit

| Check | Result |
|-------|--------|
| Non-empty assertions | PASS |
| No over-mock of SUT | PASS |
| No tautology assertions | PASS |

## Contract Consistency

| Contract | Status |
|----------|--------|
| openapi.yaml paths match test URLs | PASS |
| Response field assertions match schemas | PASS |
| HTTP status codes match spec | PASS |

## Name-Independence Audit

| Check | Result |
|-------|--------|
| No hard-coded internal class names | PASS |
| URL paths derived from openapi.yaml | PASS |
| No DOM selector hard-coding | PASS (backend only) |

## Self-Validation Gate

- [x] Contract consistency: PASS
- [x] Name independence: PASS
- [x] Blind-write testability: PASS
- [x] Requirement coverage: PASS

## Conclusion

Integration test gate **PASSED**. All P0 user stories covered.
Gate 3 (UAT) is **unlocked**.
