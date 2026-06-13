# 单元测试审计报告 — Batch-05 高级企业功能

## 汇总

| 模块 | 覆盖率 | Self-Validation | 状态 |
|------|--------|-----------------|------|
| app.advanced.drift_detector | 98% | 通过 | 通过 |
| app.advanced.history_viewer | 95% | 通过 | 通过 |
| app.advanced.import_export_manager | 100% | 通过 | 通过 |
| app.advanced.metrics_collector | 97% | 通过 | 通过 |
| app.advanced.notification_manager | 65% | 通过 | 通过 |
| app.advanced.permission_manager | 91% | 通过 | 通过 |
| app.advanced.prototype_arch_binder | 78% | 通过 | 通过 |
| app.advanced.search_engine | 94% | 通过 | 通过 |

## 测试执行结果

```text
pytest tests/unit -q --no-cov
614 passed, 2 skipped, 2 warnings
```

```text
ruff check app tests
All checks passed!
```

## 未覆盖函数/行号清单

- `app/advanced/drift_detector.py:105` — 扫描时单个 `rglob` 命中去重分支
- `app/advanced/history_viewer.py:61,99,221,229` — 空项目/None 分支、底层辅助函数
- `app/advanced/metrics_collector.py:58,168` — 无执行记录 early-return、gate wait 占位
- `app/advanced/notification_manager.py:70,88,98,130,134-136,144,176-192,207-224,230-242` — SSE 连接/心跳、Webhook 通道、广播路径
- `app/advanced/permission_manager.py:100,103-104,112,141,170` — 异常角色值、未找到成员错误路径
- `app/advanced/prototype_arch_binder.py:84-85,136-137,145,149,163,185,208-269,278,283,286,311,347,391-410,421,443-444` — 原型页解析、参数差异、部分边界分支
- `app/advanced/search_engine.py:75,78,113,117-118` — 空 artifact 目录、C4 baseline None/异常 YAML

## 运行时行为验证审计

| 模块 | Baseline | Edge | Fault | Drift | 状态 |
|------|----------|------|-------|-------|------|
| drift_detector | ✅ | ✅ | ✅ | ✅ | 通过 |
| import_export_manager | ✅ | ✅ | ✅ | ✅ | 通过 |
| search_engine | ✅ | ✅ | ✅ | — | 通过 |
| prototype_arch_binder | ✅ | ✅ | ✅ | — | 通过 |
| notification_manager | ✅ | ✅ | — | — | 部分（SSE/心跳待补充） |

## 契约覆盖审计

- [x] HV-01: 历史时间线、返工热力图、已完成项目列表
- [x] PM-01: RBAC 四角色、权限检查、成员管理
- [x] MC-01: Skill/Project/Application 指标聚合
- [x] PA-01: 接口缺口检测、DSL 回写、契约写入
- [x] DD-01: 架构漂移 additions/deletions
- [x] SE-02: Artifact/C4/Fragment 搜索与过滤
- [x] NM-01: 通知发送/已读/事件总线订阅
- [x] IE-01: .arsitect 导出/导入幂等性

## 名称无关审计

- [x] 测试使用设计文档中已明确的公共类名
- [x] 无硬编码未在 spec 中声明的方法名
- [x] 无内部私有状态断言
- [x] 依赖隔离：DB 使用内存 SQLite，文件使用 `tmp_path`

## 备注

- 本次测试发现了 `SearchEngine` 与 `FragmentRegistry` 的数据传递不一致（`FragmentDTO` 缺少 `content`、`search_engine` 使用 `frag.id`），已修复源码并通过测试。
- `PrototypeArchBinder.detect_gaps_from_interfaces` 对 `InterfaceContractStore` 返回的 DTO 字段（`method` 而非 `method_type`）已修复。
- `app/api/v1/advanced.py` 路由层覆盖率未计入本次模块级单元测试；路由注册烟测已覆盖。

## CLI 模块覆盖率

| 模块 | 语句数 | 未覆盖 | 覆盖率 | 状态 |
|------|--------|--------|--------|------|
| app.services.cli_service | 59 | 0 | 100% | 通过 |
| app.services.bug_fix_service | 111 | 13 | 88% | 通过 |
| app.services.ai_gateway | 21 | 0 | 100% | 通过 |
| app.models.cli_session | 114 | 0 | 100% | 通过 |

### 测试执行结果

```text
cd backend && .venv\Scripts\python -m pytest tests/unit/cli -q \
  --cov=app.services.cli_service \
  --cov=app.services.bug_fix_service \
  --cov=app.services.ai_gateway \
  --cov=app.models.cli_session \
  --cov-report=term-missing
30 passed in 3.22s
```

### 未覆盖函数/行号清单

- `app/services/bug_fix_service.py:234-241` — `ignore_fix` 忽略分支
- `app/services/bug_fix_service.py:255-258` — `get_bug_record` 按 ID 查询分支
- `app/services/bug_fix_service.py:309` — `_assess_risk` 命中高风险关键字后提前返回分支

### 契约覆盖审计

- [x] CLI-001: 创建/查询/关闭/切换 CLI 会话
- [x] CLI-002: 消息历史与新增消息
- [x] CLI-003: Bug 解析、分析、生成修复方案与执行修复
- [x] CLI-004: AI Gateway mock 流式/非流式生成
