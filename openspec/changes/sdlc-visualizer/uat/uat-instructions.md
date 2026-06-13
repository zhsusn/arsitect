# UAT 执行指南：Arsitect SDLC Visualizer MVP

> 对应变更：`sdlc-visualizer`  
> 验证日期：2026-06-12  
> 执行人：{人工填写}  
> 辅助：AI 生成的检查清单与报告模板

---

## 1. 预览环境信息

| 项目 | 配置 |
|------|------|
| 后端服务 | `http://localhost:8000` (FastAPI + Uvicorn) |
| 前端应用 | `http://localhost:5173` (React 19 + Vite) |
| API 文档 | `http://localhost:8000/docs` (Swagger UI) |
| 数据库 | SQLite 本地文件 (`data/sdlc-visualizer.db`) |
| 变更分支 | `main` (尚未打 tag，Git 无初始 commit) |

### 1.1 启动步骤

```bash
# 终端 1：启动后端
cd backend
python main.py
# 或 uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2：启动前端
cd frontend
npm run dev
```

### 1.2 环境重置方法

若测试过程中数据污染，执行以下步骤重置：

```bash
# 方式 A：删除 SQLite 数据库文件（最彻底）
cd backend
rm data/sdlc-visualizer.db
# 重启后端服务，数据库会自动重新创建

# 方式 B：仅清空测试项目数据（保留系统表）
# 通过 Swagger UI 调用 DELETE 接口逐一清理，或重启后端前删除 db 文件
```

> ⚠️ **注意**：当前 MVP 阶段无数据备份机制，重置后所有数据丢失，请确认后再执行。

---

## 2. 测试账号与权限

当前 MVP **尚未实现 RBAC 权限体系**，所有接口无需登录即可访问。UAT 执行时无需账号密码。

| 角色 | 说明 | 当前状态 |
|------|------|----------|
| Tech Lead | 旁路审批授权人 | 未实现角色校验，任何请求均可审批 |
| Security Officer | 旁路审批授权人 | 同上 |
| 申请人 | 提交旁路申请 | 无需认证 |
| 补审人 | 事后补审 | 无需认证 |

> 🟡 **P1 迭代项**：RBAC 与登录体系将在后续迭代中补充，当前 UAT 仅验证 API 功能正确性，不验证权限拦截。

---

## 3. 需重点关注的 P0 链路

以下链路为本次发布的核心能力，**必须逐条走通**：

1. **BindingRule CRUD**：创建 → 列表 → 获取 → 更新 → 删除
2. **Bypass 审批闭环**：申请 → 列表 → 审批通过
3. **OpenUISpec CRUD**：创建 → 列表 → 获取 → 更新 → 删除
4. **Sketch CRUD**：创建 → 列表 → 获取 → 更新 → 删除
5. **Wireframe CRUD**：创建 → 列表 → 获取 → 更新 → 删除
6. **跨模块数据隔离**：同一项目下各模块数据互不干扰

---

## 4. 前端页面可用性说明

当前前端处于 **MVP 骨架阶段**，以下页面可能尚未实现或仅为占位：

| 页面 | 来源 DR | 前端状态 | UAT 替代方式 |
|------|---------|----------|-------------|
| Gate 阻塞页 → 旁路申请（Pg_001） | DR-017 | 未实现 | Swagger UI `POST /gates/{id}/bypass` |
| 授权审批页（Pg_002） | DR-017 | 未实现 | Swagger UI `POST /bypass-applications/{id}/approve` |
| 补审工作台（Pg_004） | DR-017 | 未实现 | Swagger UI `GET /projects/{id}/bypass-applications` |
| 原型工作台（Pg_001） | DR-018 | 未实现 | Swagger UI `POST /projects/{id}/open-ui-specs` |
| 线框图总览页（Pg_001） | DR-019 | 未实现 | Swagger UI `POST /projects/{id}/wireframes` |
| 单页线框图预览（Pg_002） | DR-019 | 未实现 | — |

> **UAT 策略**：本次 UAT 以 **API 契约验证**为主，前端页面验证为辅。若前端页面已实现，优先通过页面操作；若未实现，使用 Swagger UI 完成同等验证，并在 `uat-report.md` 中记录前端缺失项。

---

## 5. 异常分支模拟指南

| 异常场景 | 模拟方法 | 观察要点 |
|----------|----------|----------|
| 非法枚举值 | 在 Swagger UI 中手动构造 `status="INVALID"` 的请求体 | 返回 400，响应体包含可读错误信息 |
| 空列表 | 查询一个刚创建、无子记录的项目 | 返回 200 + `[]`，而非 404 或 500 |
| 记录不存在 | 使用随机 UUID 作为 ID 调用 GET / PATCH / DELETE | 返回 404，响应体包含 `"detail": "...not found..."` |
| 输入长度不足 | Bypass 申请时 `reason="x"`（仅 1 字符） | 返回 422，包含字段级校验错误 |
| 跨项目数据隔离 | 创建 Project A 和 Project B，在 A 中创建记录，查询 B 的列表 | B 的列表不应出现 A 的记录 |

---

## 6. 执行顺序建议

```
Step 1: 环境启动与健康检查（5 min）
  └─ 启动后端 + 前端
  └─ 访问 /health、/docs，确认服务正常

Step 2: 单模块 CRUD 验证（20 min）
  └─ BindingRule → Bypass → OpenUISpec → Sketch → Wireframe
  └─ 每个模块：Create → List → Get → Update → Delete

Step 3: 异常路径验证（10 min）
  └─ 非法枚举、空列表、记录不存在、输入长度不足

Step 4: 跨模块闭环验证（10 min）
  └─ 同一项目下创建各模块记录
  └─ 验证列表隔离、更新生效、删除彻底

Step 5: 结果记录（5 min）
  └─ 填写 uat-report.md
  └─ 勾选 user-stories-checklist.md
```

---

## 7. 问题反馈模板

若在 UAT 过程中发现问题，请按以下格式记录：

```markdown
### 问题 {编号}
- **关联需求**：FR-XXX / US-XXX
- **严重级别**：🔴 P0 阻塞 / 🟡 P1 遗留
- **复现步骤**：
  1. ...
  2. ...
- **预期结果**：...
- **实际结果**：...
- **截图/日志**：...
- **环境信息**：浏览器版本、操作系统、前后端 commit（如有）
```
