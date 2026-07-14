# Conventional Commits 规范（本 Skill 的输出标准）

模型生成、脚本兜底校验均以此为准。

## 格式

```
<type>(<scope>): <简述>

<可选正文>

<可选 footer>
```

## type 取值

| type | 含义 |
|------|------|
| feat | 新功能 |
| fix | 修 bug |
| docs | 文档 |
| style | 代码格式（不改逻辑） |
| refactor | 重构（非 feat / 非 fix） |
| perf | 性能优化 |
| test | 测试相关 |
| build | 构建系统 / 依赖 |
| ci | CI 配置 |
| chore | 杂项 |
| revert | 回滚 |

## scope

受影响的模块名（如 `api`、`auth`、`ui`、`memory`）。**不确定时省略**，不要硬造。

## 简述

- 祈使句、现在时：`add export endpoint`（而非 `added`）
- 说明「做了什么」，不说明「怎么做」
- 尽量 ≤50 字符，结尾不加句号

## 正文（可选）

- 改动动机、替代方案、副作用
- 每行以 `-` 开头
- 解释 **why**，不重复 diff 内容

## 示例

```
feat(api): 新增画布导出 PNG 接口

- 复用 render_service 渲染逻辑
- 返回临时 URL，TTL 1 小时
```

```
fix(auth): token 过期未清空导致跨 run 请求串扰

net_count 状态机在 finalize 前未重置，复用了上一轮 token。
```

```
refactor(memory): 偏好落库改用 net_count 状态机
```

## 中文项目适配

中文项目可直接用中文简述，**type 仍用英文枚举**：

```
feat(修图): 支持按场景类型分桶下发偏好

- image-conditional 偏好按 scene_type 隔离，避免互相污染
- 下发协议不变，仅后端分桶
```
