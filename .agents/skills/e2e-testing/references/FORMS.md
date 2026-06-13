# E2E Testing 表单与模板

> 本文件按需加载，供 SKILL.md 执行时引用。包含任务清单、覆盖矩阵、报告模板等结构化表单。

---

## 1. E2E 范围确认单

```markdown
# E2E 测试范围确认单

## 项目信息
- 前端技术栈: {Vue/React/Angular/other} + {端口}
- 后端技术栈: {FastAPI/Django/Express/other} + {端口}
- 目标环境: 本地 dev / Docker / 预览环境 / staging
- 策略: default / strict

## 已有启动资源（优先复用）
| 资源 | 路径/命令 | 说明 |
|------|-----------|------|
| Docker Compose | docker-compose.yml | 一键启动前后端 + 数据库 |
| 后端启动脚本 | backend/start-dev.sh | 本地 dev server |
| 前端 dev server | cd frontend && npm run dev | Vite/Webpack dev server |
| 已有测试 fixture | tests/conftest.py | 可直接 import 的服务 fixture |

若以上都没有，Skill 将在 conftest.py 中临时生成 subprocess 启动代码。

## P0 用户故事
| 需求编号 | 用户故事 | 是否纳入 E2E | 备注 |
|----------|----------|--------------|------|
| FR-001 | ... | 是 | 登录流程 |

## 外部依赖与 Mock 计划
| 依赖 | 类型 | Mock 方式 | 理由 |
|------|------|-----------|------|
| AI 生成接口 | 慢/不稳定 | route.fulfill | 避免真实 LLM 调用 |

## 视觉回归目标
| 页面 | 是否截图 | baseline 名 |
|------|----------|-------------|
| /projects | 是 | project-dashboard.png |

## 明确不做（反范围）
- ...
```

---

## 2. 任务清单模板

```markdown
# E2E 测试任务清单

| ID | 任务 | 覆盖需求 | 依赖 | 验证方式 | 状态 |
|----|------|----------|------|----------|------|
| E2E-01 | 搭建服务生命周期 fixture | — | 环境可启动 | 健康检查通过 | pending |
| E2E-02 | 实现 LoginPage POM | FR-001 | E2E-01 | POM 可实例化 | pending |
| E2E-03 | 编写登录黄金流程 | FR-001 | E2E-02 | pytest 通过 | pending |
```

---

## 3. 覆盖矩阵模板

```markdown
# E2E 覆盖矩阵

| 需求编号 | 用户故事 | E2E 测试 ID | 测试文件 | 状态 |
|----------|----------|-------------|----------|------|
| FR-001 | 作为用户，我可以登录 | E2E-0101 | flows/test_golden_login.py | PASS |
```

---

## 4. E2E 报告模板

```markdown
# E2E 测试报告

> 生成时间: {ISO8601}
> 策略: {default/strict}
> 环境: {本地/预览/staging}

## 总体结果
| 项目 | 数值 |
|------|------|
| 总用例数 | N |
| 通过 | N |
| 失败 | N |
| 通过率 | N% |

## P0 用户故事覆盖
| 需求编号 | 用户故事 | 覆盖测试 | 状态 |
|----------|----------|----------|------|
| FR-001 | ... | E2E-0101 | PASS |

## Mock 清单
| 接口 | Mock 理由 | 是否需补充真实 Provider 验证 |
|------|-----------|------------------------------|
| /api/v1/designs/generate | 慢/不稳定 | strict 模式下需要 |

## 视觉回归差异
| 页面 | baseline | diff | 状态 |
|------|----------|------|------|
| /projects | project-dashboard.png | 无 | PASS |

## Flaky 风险与建议
1. ...

## CI 接入命令
```bash
pytest tests/e2e/flows/ -v --tracing=retain-on-failure
```
```

---

## 5. 发布前 E2E Checklist

- [ ] 所有 P0 黄金流程通过
- [ ] 控制台无 Error 级别日志
- [ ] 关键页面截图与 baseline 无差异（或差异已确认）
- [ ] Mock 清单已记录 rationale
- [ ] 失败时截图 / trace / 视频可正常收集
- [ ] CI 配置已验证通过
- [ ] 追溯矩阵 `tests/TRACEABILITY.csv` 已更新
