# Backend Design Guide

本文件供 `detailed-design` Skill 在生成 module-design.md 第 1/2/3/4/5 章时按需加载。

---

## 1. 分层架构模板

每个后端模块必须明确以下四层，并禁止跨层调用：

| 层级 | 职责 | 命名约定 | 允许依赖 |
|---|---|---|---|
| **Controller** | 接收 HTTP/gRPC 请求，参数校验，路由分发 | `XxxController` / `xxx_handler.py` | Service |
| **Service** | 业务逻辑编排，事务边界，领域事件发布 | `XxxService` / `xxx_service.py` | Repository, Domain, 其他 Service |
| **Repository** | 数据访问抽象，SQL/ORM 操作，缓存读写 | `XxxRepository` / `xxx_repo.py` | 仅基础设施（DB/Cache） |
| **Domain** | 纯业务实体、值对象、领域服务、不变量 | `XxxEntity` / `xxx_domain.py` | 仅标准库/语言特性 |

> 禁止：Controller 直接调用 Repository；Domain 层依赖基础设施。

---

## 2. 类/函数设计规范

- 类职责单一（SRP）， public 方法 ≤ 7 个
- 函数签名必须包含类型注解（Python）或完整泛型（Java/Kotlin）
- 核心算法逻辑用伪代码或流程图表达，禁止直接输出可运行生产代码
- 依赖关系用 Mermaid `classDiagram` 表达

### 伪代码格式示例

```text
算法: 订单金额计算
输入: items: List[OrderItem], coupons: List[Coupon]
输出: FinalAmount

1. 校验 items 非空，否则抛 ValidationError
2. 计算商品原价: subtotal = sum(item.price * item.quantity)
3. 按优先级排序 coupons（满减 > 折扣 > 直降）
4. 逐条应用 coupon，记录已用 coupon_id
5. 计算运费: shipping = subtotal >= threshold ? 0 : base_fee
6. 返回 FinalAmount(subtotal, discount, shipping, total)
```

---

## 3. 代码风格速查

### Python（Google Style）
- 命名：`snake_case`（函数/变量），`PascalCase`（类），`UPPER_SNAKE_CASE`（常量）
- 类型注解：必选；返回值类型不可省略
- Docstring：Google 风格（Args/Returns/Raises）
- 行宽：100 字符

### Java（Alibaba Style）
- 命名：`UpperCamelCase`（类），`lowerCamelCase`（方法/变量）
- 包装类型：POJO 属性必须用包装类（`Integer` 而非 `int`）
- 注释：类/方法必须有 Javadoc，复杂逻辑加行内注释
- 行宽：120 字符

---

## 4. OpenAPI 3.1 片段示例

模块级接口定义必须包含以下结构的 YAML 片段：

```yaml
paths:
  /api/v1/orders:
    post:
      summary: 创建订单
      operationId: createOrder
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                  format: uuid
                  description: 用户唯一标识
              required: [user_id]
      responses:
        '201':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '400':
          description: 参数校验失败
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```

> 红线：禁止动词 URI（`/getOrder`、`/createUser`）；必须包含完整的 request/response/error 结构。

---

## 5. DDL 规范

### CREATE TABLE 模板

```sql
CREATE TABLE IF NOT EXISTS `table_name` (
  `id`          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  `biz_id`      VARCHAR(64) NOT NULL COMMENT '业务唯一标识',
  `status`      TINYINT NOT NULL DEFAULT 0 COMMENT '状态: 0-待处理 1-处理中 2-成功 3-失败',
  `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_biz_id` (`biz_id`),
  KEY `idx_status_created_at` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表业务说明';
```

### 索引策略
- 每个表必须有 `created_at` 索引或复合索引前缀
- 区分度 < 10% 的字段禁止单独建索引
- 联合索引字段顺序：等值查询在前，范围查询在后

---

## 6. 公共组件引用格式

若依赖 shared/design.md 中的公共组件，在模块设计中按以下格式列出：

```markdown
### 依赖公共组件

| 组件名 | 引用路径 | 使用场景 |
|---|---|---|
| `IdempotencyKeyGenerator` | `../shared/design.md#IdempotencyKeyGenerator` | 生成幂等键 |
```

---

## 7. 状态机规范

- 使用 Mermaid `stateDiagram-v2` 语法
- 每个子状态块 `{ ... }` 必须闭合
- 状态转换标注触发条件，含特殊字符时加双引号
- 必须包含 `[*]` 起始状态和至少一个终止状态
- 异常分支不可省略（如支付失败、超时关闭）

### 与全局状态机映射格式

```markdown
### 全局状态映射

| 模块局部状态 | 全局状态 | 说明 |
|---|---|---|
| `OrderPending` | `GlobalPending` | 创建后待支付 |
```

---

## 8. 测试策略模板

每个模块的测试策略必须包含：

### 单元测试用例表

| 用例ID | 场景 | Given | When | Then | 追溯AC |
|---|---|---|---|---|---|
| TC-001 | 正常创建订单 | 用户已登录，商品库存充足 | 调用 create_order | 返回订单号，库存扣减1 | AC-1.1 |

### 集成测试场景表

| 场景ID | 场景描述 | 涉及模块 | Mock策略 | 期望结果 |
|---|---|---|---|---|
| IT-001 | 支付回调通知 | order + payment | Mock 支付网关 | 订单状态变更为已支付 |

### 边界条件清单
- [ ] 空值 / null 输入
- [ ] 越界值（最大值+1、最小值-1）
- [ ] 并发冲突（乐观锁/悲观锁）
- [ ] 超时 / 降级 / 熔断场景
