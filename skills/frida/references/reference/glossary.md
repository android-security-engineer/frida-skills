---
name: glossary
description: Frida terminology glossary — Gum, GumJS, gadget, server, agent, host, trampoline, stalker, interceptor, ART, dispatch queue, eternalize, QJS/V8, and other terms an agent needs to disambiguate.
type: summary
---

# Glossary

| Term | Meaning |
| --- | --- |
| **Gum** | The low-level C instrumentation library underlying everything. |
| **GumJS** | The JS engine + bindings that run your agent inside the target. |
| **agent** | Your JavaScript, running inside the target process via GumJS. |
| **host** | The CLI / Python / Node / MCP client that loads the agent and receives messages. |
| **frida-server** | A daemon run on a device that accepts host connections and injects agents. |
| **frida-gadget** | A shared library embedded into an app (no separate server); for non-rooted/re-signed targets. |
| **trampoline** | The code stub Frida writes at a hook target to detour calls to the dispatcher. |
| **Interceptor** | The hooking API: `attach`/`replace`/`revert`/`flush`. |
| **Stalker** | Per-thread code tracer that rewrites the instruction stream as it runs. |
| **CModule** | In-process compiled C for fast, inline instrumentation. |
| **NativePointer** | The JS handle for a native address; all memory read/write goes through it. |
| **QJS / V8** | The two JS runtimes; QuickJS is default, V8 is opt-in (`--runtime=v8`). |
| **ART** | Android Runtime — the VM executing dex bytecode; the Java bridge talks to it. |
| **dispatch queue** | The GCD queue ObjC code runs on; `ObjC.schedule` targets one. |
| **eternalize** | `Script.eternalize()` — detach the agent's lifetime from the host so it survives disconnect. |
| **spawn gating** | Spawn the app paused, install hooks, then resume — so early code is caught. |
| **version skew** | Host `frida` and device `frida-server` being different versions; the top failure cause. |
