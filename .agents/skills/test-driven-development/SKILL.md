---
name: test-driven-development
description: 当用户在 executing-plans 编码阶段、需要为单个开发任务执行 RED-GREEN-REFACTOR 循环，或用户提到'先写测试'、'TDD'、'测试驱动'时触发。任务级测试先行方法论，驱动接口设计。
---

# Test-Driven Development (TDD)

## 适用场景

- executing-plans 的每个任务内部，作为编码内循环执行
- 新功能实现
- Bug 修复
- 重构
- 行为变更

**例外情况（需请示用户）：**
- 一次性原型
- 生成的代码
- 配置文件

## 核心原则

**先写测试，看它失败，再写最小实现。**

如果你没看到测试失败，你就不知道它测的是不是正确的东西。

**违反规则的字面含义，就是违反规则的精神。**

## 代码风格规范

生成任何源代码（生产代码与测试代码）时，必须遵循对应语言的代码风格：
- **Python**：遵循 `python-google-style` Skill（Google Python Style Guide，行宽80、4空格缩进、类型注解、Google风格docstring等）
- **Java**：遵循 `java-alibaba-style` Skill（阿里巴巴Java开发手册，命名规范、OOP规约、集合处理、异常日志等）
- **其他语言**：使用该语言社区默认风格（TypeScript/ESLint+Prettier、Go/gofmt、Rust/rustfmt 等）

## 铁律

```
禁止在没有失败测试的情况下编写生产代码
```

先写实现后补测试？删掉实现，重新开始。

**没有例外：**
- 不要留着当"参考"
- 不要"适配"它到测试中
- 不要看它
- 删掉就是删掉

从测试重新开始实现。

## 与上下游衔接

| 衔接点 | 动作 |
|--------|------|
| 上游: executing-plans | 每个开发任务的内部执行纪律，由 executing-plans 在 Step 3 调用 |
| 横向: unit-test | TDD 产出的内联测试在 Batch 完成后由 unit-test 统一整理到 `tests/unit/`；运行时行为验证测试整理到 `tests/unit/runtime/` |
| 横向: self-check | GREEN 阶段完成后可调用 self-check 验证代码与设计一致性 |

## RED-GREEN-REFACTOR 循环

### R - RED（写失败测试）

基于当前任务的验收标准 + api-spec.md 中的接口定义，先写测试。

- 一个行为，一个测试
- 命名清晰（名称中出现 "and"？拆分它）
- 使用真实代码（除非不可避免，否则不用 mock）

**要求：**
- 测试必须失败（验证测试本身有效）
- 禁止先写实现代码后补测试
- 测试文件临时存放：`.kimi/temp-tests/{任务ID}_red.py`

**运行时行为验证 RED 要求（V3.2 新增）：**
如果当前任务涉及 I/O 边界（DB、网络、文件、缓存）或状态变更，RED 阶段必须额外编写运行时行为验证测试：
- 验证函数执行前后的状态变化（数据库记录、文件系统、缓存状态）
- 验证异常抛出时的资源回滚行为
- 使用 Mock/Spy 验证外部依赖的调用次数和参数
- 包含至少一个边界输入探测（Edge Probe）

运行时行为验证测试临时存放：`.kimi/temp-tests/{任务ID}_runtime_red.py`

**三层安全门控（TDD RED 阶段应用，V3.2 新增）**：

运行任何涉及真实 I/O 的 RED 测试前，必须通过以下门控：

| 门控 | 检查项 | TDD 阶段处理 |
|------|--------|-------------|
| **Destination** | 探测目标是否为本地/测试环境/只读端点？ | 禁止直接探测生产环境；使用 Testcontainers / WireMock / SQLite :memory: 替代 |
| **Intent** | 用户是否确认运行时验证计划？ | 展示探测矩阵摘要（含探测点数量和类型），等待显式确认 |
| **Data** | 是否涉及真实用户数据、付费资源、环境变量？ | 自动脱敏；列出具体变量名，要求单独授权 |

若任一门控未通过，将运行时验证测试降级为纯 Mock 测试，并标记 `[GATE_SKIPPED]`。

**好示例：**
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

**坏示例：**
```typescript
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```

### Verify RED - 验证失败

**强制步骤，不可跳过。**

```bash
npm test path/to/test.test.ts
```

确认：
- 测试失败（不是报错）
- 失败信息符合预期
- 失败原因是功能缺失（不是拼写错误）
- 运行时行为验证测试是否先写且确实失败（如状态探测、Spy 验证）？
- 故障注入测试是否触发了预期的异常路径？

**测试通过了？** 你在测试已有行为。修正测试。

**测试报错了？** 修正错误，重新运行直到正确失败。

### G - GREEN（最小实现）

编写最简单、最丑但能让测试通过的实现。

- 禁止在 GREEN 阶段优化代码结构、提取公共函数、重命名变量
- 禁止处理当前任务范围外的边界情况
- 若发现相邻问题，记入 `NOTICED BUT NOT TOUCHING`，不修复

**测试失败后**，编写最小代码让它通过。

**运行时验证 GREEN 要求（V3.2 新增）：**
若 RED 阶段包含运行时行为验证测试，GREEN 阶段的最小实现必须确保：
- 状态变更符合预期（Pre-state → Post-state 断言通过）
- 异常路径不泄漏资源（事务回滚、连接关闭、临时文件清理）
- Spy/Mock 验证的外部依赖调用次数和参数正确

**好示例：**
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```

**坏示例：**
```typescript
async function retryOperation<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number) => void;
  }
): Promise<T> {
  // YAGNI - 过度工程化
}
```

### Verify GREEN - 验证通过

**强制步骤。**

```bash
npm test path/to/test.test.ts
```

确认：
- 测试通过
- 其他测试仍通过
- 输出干净（无报错、无警告）

**测试失败？** 修正代码，不是测试。

**其他测试失败？** 立即修复。

### R - REFACTOR（安全重构）

在测试全部通过的前提下，清理代码：

- 允许：提取函数、重命名变量、消除重复、优化导入
- 禁止：修改接口签名、新增功能、处理 `NOTICED BUT NOT TOUCHING` 中的问题
- 每次重构后必须重新运行测试，确保仍通过
- 重构后必须重新运行**运行时行为验证测试**，确认状态变更和副作用未漂移

### 重复

下一个失败测试，下一个功能。

## TDD 门控检查点

每个任务完成后必须确认：

- [ ] RED 阶段测试是否先写且确实失败？
- [ ] GREEN 阶段实现是否最小化（无过度设计）？
- [ ] REFACTOR 后测试是否全部通过？
- [ ] 当前任务代码是否新增文件（Rollback-Friendly）？
- [ ] `NOTICED BUT NOT TOUCHING` 清单是否已更新？
- [ ] 运行时行为验证测试是否先写且确实失败（如状态探测、Spy 验证）？
- [ ] 异常路径是否经过运行时验证（资源回滚、无脏数据）？
- [ ] 运行时验证测试是否处理了非确定性因素（固定随机种子、语义等价断言）？
  - 若测试涉及随机数、时间戳、并发 ID，是否固定了种子（`seed=42`）？
  - 是否使用语义等价断言（如 `abs(a - b) < epsilon`、`status in ["TIMEOUT", "PENDING"]`）替代精确值断言？

## 为什么顺序很重要

**"我写完再补测试来验证"**

事后写的测试立即通过。立即通过证明不了任何东西：
- 可能测错了东西
- 可能测的是实现，不是行为
- 可能漏了你忘记的边界情况
- 你从没看到它抓住 bug

先写测试迫使你看到测试失败，证明它确实测了某些东西。

## 常见合理化借口

| 借口 | 现实 |
|------|------|
| "太简单了不用测" | 简单代码也会坏。测试只需 30 秒。 |
| "我后面再测" | 后面写的测试立即通过，证明不了什么。 |
| "已经手动测过了" | 手动测试是临时性的，没有记录，无法重跑。 |
| "删掉 X 小时的工作太浪费了" | 沉没成本谬误。不能信任的代码才是浪费。 |
| "TDD 太教条，我要务实" | TDD 就是务实：提前发现 bug 比事后调试快。 |

## 红旗 - 停下来重新开始

- 先写代码后写测试
- 测试立即通过
- 无法解释测试为什么失败
- "就这一次"的合理化
- "留着当参考"或"适配现有代码"
- "TDD 太教条，我这是务实"

**所有这些意味着：删掉代码，从 TDD 重新开始。**

## 测试反模式参考

当添加 mock 或测试工具时，阅读 `@testing-anti-patterns.md` 避免常见陷阱：
- 测试 mock 行为而不是真实行为
- 向生产类添加仅用于测试的方法
- 在不理解依赖的情况下 mock

## 调试集成

发现 bug？写重现它的失败测试。遵循 TDD 循环。测试证明修复并防止回归。

永远不要在没有测试的情况下修复 bug。

## Gotchas

- **测试文件时间戳检查**：若代码文件修改时间早于测试文件，拒绝进入 GREEN 阶段
- **禁止保留未测试的实现**：先写实现后补测试 = 技术债务，必须删除实现重新开始
- **测试必须先失败**：跳过 RED 验证 = 你不知道测试是否有效
- **GREEN 阶段禁止优化**：重构必须在测试通过后进行，不得在 GREEN 阶段顺手优化
- **任务范围外边界不处理**：发现相邻问题记入 `NOTICED BUT NOT TOUCHING`，不当场修复
- **测试必须真实**：优先使用真实代码，mock 仅用于隔离外部依赖
- **每个任务一个 TDD 循环**：不要在一个任务内堆积多个功能的实现再统一补测试
- **运行时验证的环境隔离**：RED 阶段编写的行为探测测试必须确保环境隔离（事务回滚、临时目录、Mock 重置），禁止在 TDD 循环中污染共享状态或产生不可逆副作用
