# Product Localization Glossary — English / 简体中文

## Purpose

This glossary is the approved terminology contract for the Founder workspace.
It governs product copy in Sprint 162 and later M29 visual work.

It does not translate or replace raw API values, IDs, artifact contents, user
text, or audit evidence.

## Usage Rules

1. Use the approved Chinese term consistently across navigation, headings,
   buttons, forms, states, and help text.
2. Preserve raw transport values where they carry audit or governance meaning.
3. Do not translate product terms in a way that implies real-money trading,
   automatic approval, recommendation, or executed lifecycle change.
4. Prefer plain product language over literal technical translation.
5. Do not translate identifiers such as `job_id`, `run_id`, artifact keys, UUIDs,
   strategy names, or idempotency-key values.

## Core Product Terms

| English | Approved Simplified Chinese | Rejected / discouraged alternatives | Notes |
|---|---|---|---|
| Founder Workspace | 创始人工作台 | 创始人空间、老板后台 | “工作台” communicates an operational product surface. |
| AI Quant Decision Workspace | AI 量化决策工作台 | AI 量化交易终端、AI 自动决策平台 | Must not imply autonomous trading or approval. |
| Standard Workspace | 标准工作区 | 正式环境、生产环境 | The local standard workspace may still contain non-production data; do not call it production. |
| Demo Workspace | 演示工作区 | 测试环境、模拟盘 | “演示工作区” identifies disposable example evidence without confusing it with paper trading itself. |
| Workspace mode | 工作区模式 | 环境模式 | Use for Standard/Demo identity. |
| Overview | 总览 | 首页、仪表盘 | “总览” remains valid until S164 establishes the Founder Dashboard. |
| Founder Dashboard | 创始人看板 | 老板大屏、交易仪表盘 | Must remain decision/review oriented rather than a live market terminal. |
| Strategy | 策略 | 战法 | Raw strategy `name` remains unchanged. |
| Strategy definition | 策略定义 | 策略说明书 | Use for registered backend-owned strategy metadata. |
| Research | 研究 | 研判 | Generic product area. |
| Research run | 研究运行 | 回测任务 | A research run may include backtest behavior, but the contract name is broader. |
| Research evidence | 研究证据 | 研究材料、研究结果 | “证据” preserves governance meaning; source data remains authoritative. |
| Backtest | 回测 | 历史模拟 | Use “回测” where the source concept is explicitly backtesting. |
| Governance evidence | 治理证据 | 审批材料、合规材料 | Must not imply that evidence itself is approval. |
| Report artifact | 报告制品 | 报告文件、报告附件 | “制品” preserves artifact-contract meaning; UI may explain it as a saved report record. |
| Evidence manifest | 证据清单 | 证据文件、证据目录 | A manifest is a structured list/reference contract, not the underlying evidence payload. |
| Reference | 引用 | 链接 | Many references are unresolved text and are not clickable links. |
| Artifact | 制品 | 文件 | Use “制品” in technical/audit contexts; explanatory copy may say “已保存制品”. |
| Paper Trading | 模拟交易 | 纸上交易、仿真交易、实盘模拟 | “模拟交易” is the primary user-facing term. It must not imply real capital. |
| Paper Run | 模拟运行 | 模拟交易、回测运行 | A bounded execution request/result, not the overall Paper Trading product area. |
| Paper Job | 模拟任务 | 交易任务、作业 | “模拟任务” is clearer for the Founder. Raw API/entity names remain `paper_job`. |
| Paper Job submission | 提交模拟任务 | 发起交易 | Submission creates queued state only and does not execute automatically. |
| Portfolio Record | 组合记录 | 投资组合、持仓报告 | A saved result view, not capital allocation advice. |
| Portfolio Result | 组合结果 | 收益结果 | Do not narrow the result to return/profit. |
| Comparison | 对比分析 | 排名、优选 | Comparison is ordered juxtaposition without ranking or recommendation. |
| Lifecycle | 生命周期 | 生命周期状态机 | Product copy should remain understandable; raw states remain visible. |
| Lifecycle Review | 生命周期审查 | 生命周期审批 | Review does not imply approval. |
| Lifecycle state | 生命周期状态 | 策略状态 | Raw domain state such as `research_review` remains visible. |
| Proposal | 提案 | 申请、审批单 | A proposal is explicitly non-executing. |
| Transition proposal | 状态转换提案 | 状态变更申请 | Do not imply that the state has changed. |
| Human Review | 人工审查 | 人工审批 | Review may be deferred or rejected and does not always approve. |
| Human Decision Evidence | 人工决策证据 | 审批结果、决策结论 | The record is governance evidence, not proof of runtime execution. |
| Review outcome | 审查结果 | 审批结果 | Raw outcome remains visible. |
| Result | 结果 | 成果 | Generic product label. |
| Result available | 结果可用 | 已生成收益 | Availability does not imply favorable performance. |
| Attempt | 尝试记录 | 执行次数 | The persistent entity is an audited attempt, not only a counter. |
| Audit | 审计信息 | 日志 | Audit records are structured product evidence; logs may be separate. |
| Request ID | 请求 ID | 请求编号 | Preserve exact value. |
| Schema version | 结构版本 | 模式版本 | Raw numeric/string version remains visible. |
| Idempotency Key | 幂等键 | 去重键、唯一键、密码 | Explain that it identifies replay-safe submission; it is not a password or job ID. |

## Actions

| English | Approved Simplified Chinese | Notes |
|---|---|---|
| View | 查看 | Read-only navigation. |
| Inspect | 检查 | Use when reviewing exact saved evidence or audit detail. |
| Review | 审查 | Do not automatically translate as “审批”. |
| Submit | 提交 | Submission does not imply execution. |
| Submit queued job | 提交排队任务 | Preferred full Paper Job action. |
| Run | 运行 | Explicitly starts the selected queued job. |
| Cancel | 取消 | Only valid where backend state permits. |
| Retry | 重试 | Requeues according to backend rules; it does not guarantee success. |
| Recover | 恢复 | Manual interrupted-job recovery; include explicit stale-time guidance. |
| Refresh | 刷新 | Manual state refresh, not polling. |
| Compare | 对比 | No ranking or recommendation. |
| Load demo example | 加载演示示例 | Populates fields only and never submits automatically. |
| Create proposal | 创建提案 | Non-executing. |
| Record human review | 记录人工审查 | Creates/returns governance evidence; it does not apply runtime state. |
| Back | 返回 | Prefer a destination in longer copy where useful. |
| Retry request | 重试请求 | Use for transient read failures, distinct from Paper Job retry. |

## Workspace and Data States

| English | Approved Simplified Chinese | Raw value display | Notes |
|---|---|---|---|
| Loading | 加载中 | Not required | A transient presentation state. |
| Empty | 暂无数据 | Not required | Explain that empty can be healthy. |
| Unavailable | 不可用 | Show error code when available | Different from empty. |
| Invalid | 无效 | Show raw identity/detail when safe | Invalid evidence/configuration must not be described as empty. |
| Not found | 未找到 | Show requested raw ID when safe | Preserve bounded not-found semantics. |
| Failed | 失败 | Show raw `failed` for audited job state | Do not translate as “亏损”. |
| Succeeded | 成功 | Show raw `succeeded` for audited job state | Success means operation completed, not profitable performance. |
| Canceled | 已取消 | Show raw `canceled` for audited job state | Preserve US spelling in transport value. |
| Queued | 排队中 | Show raw `queued` for audited job state | Submission only. |
| Running | 运行中 | Show raw `running` for audited job state | Does not imply completion. |
| Result unavailable | 结果不可用 | Show stable error/status detail | Different from a failed strategy or negative result. |
| Healthy | 运行正常 | Not required | Use for reachable configured product state, not trading performance. |
| Configured | 已配置 | Not required | Do not imply data exists. |
| Demo only | 仅供演示 | Keep warning context | Must remain persistent in Demo mode. |
| Disposable example data | 可丢弃的示例数据 | Not required | Must not be confused with real evidence. |

## Lifecycle States and Outcomes

The localized label may be shown, but the raw value remains authoritative.

| Raw value | Approved Simplified Chinese label | Meaning guardrail |
|---|---|---|
| `research_review` | 研究审查 | Does not mean research is approved. |
| `paper_review` | 模拟交易审查 | Paper Trading review only; no real execution. |
| `watchlist` | 观察名单 | Not an instruction to trade. |
| `on_hold` | 已搁置 | Work is paused; not rejected. |
| `rejected` | 已拒绝 | Human governance outcome; not an automatic model result. |
| `approved` | 已批准 | Only where the existing domain contract returns this human outcome; not runtime execution. |
| `deferred` | 暂缓 | More review/evidence may be required. |

## Paper Job Statuses

| Raw value | Approved Simplified Chinese label | Meaning guardrail |
|---|---|---|
| `queued` | 排队中 | Awaiting explicit run/runner behavior. |
| `running` | 运行中 | Claimed for execution; outcome not yet known. |
| `succeeded` | 成功 | Completed successfully; not a profitability claim. |
| `failed` | 失败 | Operational execution failure; not market loss. |
| `canceled` | 已取消 | Canceled according to backend state rules. |

## Error and Recovery Terms

| English | Approved Simplified Chinese | Notes |
|---|---|---|
| Error code | 错误码 | Preserve raw stable code. |
| Error details | 错误详情 | Only sanitized product-safe detail. |
| Recovery guidance | 恢复指引 | Must be bounded and safe. |
| Product database unavailable | 产品数据库不可用 | Show raw `product_database_unavailable`. |
| Paper artifact root unavailable | 模拟交易制品目录不可用 | Do not expose server filesystem path. |
| Research artifact root unavailable | 研究制品目录不可用 | Distinguish from an empty root. |
| Evidence artifact root unavailable | 证据制品目录不可用 | Distinguish from no manifests. |
| Demo workspace not configured | 未配置演示工作区 | Standard mode is valid; not necessarily an error on Overview. |
| Demo workspace unavailable | 演示工作区不可用 | Suggest bounded startup/verification guidance. |
| Conflict | 冲突 | Explain the exact safe next step; do not auto-overwrite. |
| Replay | 重放 | Use with idempotency explanation; not automatic rerun. |
| Safe retry | 安全重试 | Only where backend contract permits. |

## Quantitative and Audit Presentation

Do not localize or rewrite:

- strategy and symbol identifiers;
- numeric source values;
- raw decimal precision needed for audit;
- raw UTC timestamps;
- formula or metric names when they are domain identifiers;
- API field names; or
- artifact source text.

A localized label may be added:

```text
最大回撤
max_drawdown
```

When the raw identifier materially aids review, display both. Common established
financial labels such as CAGR or Sharpe ratio may retain the English abbreviation
with a Chinese explanation rather than inventing a new abbreviation.

## Tone

Chinese product copy should be:

- direct;
- neutral;
- calm;
- explicit about uncertainty and boundaries;
- free of hype;
- free of profit promises; and
- clear about when a human action is required.

Avoid language such as:

- “AI 已为你选出最佳策略”;
- “一键批准”;
- “保证安全重试” when the backend cannot guarantee it;
- “正式交易” for Paper Trading;
- “盈利结果” for a generic result; or
- “系统已变更状态” for a non-executing proposal/review record.

## Change Control

New or changed high-impact terms involving financial meaning, lifecycle,
governance, execution, or audit require review in the relevant implementation
Issue. Components must not create local synonyms that diverge from this glossary.
