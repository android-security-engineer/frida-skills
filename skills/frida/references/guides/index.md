---
name: guides-index
description: Index of end-to-end Frida workflow guides — host-side Python/Node/TypeScript bindings, building agents, message handling, project structure, testing, and CI automation.
---

# Guides — end-to-end workflows

Recipes are single scripts; guides are *workflows*: how to drive Frida from a
host language, structure a real agent, and automate runs. Read a guide when you're
building something repeatable, not a one-off hook.

## Host-side bindings
| Doc | Covers |
| --- | --- |
| [python-binding.md](python-binding.md) | The `frida` Python API: device, spawn/attach, script, messages, RPC. |
| [nodejs-binding.md](nodejs-binding.md) | `frida` on Node: async API, `frida-compile`, event handling. |
| [typescript-agent.md](typescript-agent.md) | Writing agents in TypeScript with `@types/frida-gum` + compile. |
| [message-handling.md](message-handling.md) | Robust host message loops, `send`/`recv` handshake, errors, binary. |

## Building real agents
| Doc | Covers |
| --- | --- |
| [agent-structure.md](agent-structure.md) | Structuring a multi-hook agent, config via `rpc`/parameters, cleanup. |
| [multi-file-compile.md](multi-file-compile.md) | Splitting an agent across files and bundling with `frida-compile`. |
| [reload-workflow.md](reload-workflow.md) | Fast edit→reload loops during development; `%load`, watch mode. |
| [error-handling.md](error-handling.md) | Catching agent exceptions, `Script.setGlobalAccessHandler`, defensive hooks. |

## Automation
| Doc | Covers |
| --- | --- |
| [headless-automation.md](headless-automation.md) | Fully scripted runs, timeouts, exit codes, `frida-inject`. |
| [ci-and-farms.md](ci-and-farms.md) | Running instrumentation in CI / on device farms; reproducibility. |
| [workflow-recon-to-hook.md](workflow-recon-to-hook.md) | The full loop: trace → identify → write precise hook → verify. |

## Cross-cutting concerns
| Doc | Covers |
| --- | --- |
| [session-management.md](session-management.md) | 多进程会话：attach/spawn 池化、detach 与脚本生命周期、并发会话锁。 |
| [performance-and-memory.md](performance-and-memory.md) | 热路径开销、`onEnter` 瘦身、Stalker 配额、内存与 GC 策略。 |
| [security-hardening.md](security-hardening.md) | 加固 agent、最小权限 server、防泄漏 send() 数据、隔离敏感操作。 |
| [version-migration-16-to-17.md](version-migration-16-to-17.md) | 16→17 迁移：被移除 API 全表、自动改写规则、兼容 shim。 |
