---
name: glossary
description: Frida terminology glossary — Gum, GumJS, gadget, server, agent, host, trampoline, stalker, interceptor, ART, dispatch queue, eternalize, QJS/V8, and other terms an agent needs to disambiguate.
type: leaf
---

# Glossary

Terms are grouped by what they describe, so you can find the *kind* of thing
before its name. All glossed terms are real Frida 17 concepts; where two terms
sound alike, the "Don't confuse with" note tells them apart.

## The runtime: agent ↔ host

| Term | Meaning |
| --- | --- |
| **Gum** | The low-level C instrumentation library underlying everything. |
| **GumJS** | The JS engine + bindings that run your agent inside the target. |
| **agent** | Your JavaScript, running inside the target process via GumJS. |
| **host** | The CLI / Python / Node / MCP client that loads the agent and receives messages. |
| **frida-server** | A daemon run on a device that accepts host connections and injects agents. |
| **frida-gadget** | A shared library embedded into an app (no separate server); for non-rooted/re-signed targets. |

Don't confuse **agent** with **gadget**: the agent is code (JS), the gadget is
the embedding mechanism. And don't confuse **host** with **server**: the host is
your machine's client; `frida-server` is the remote daemon on the device.

## Native instrumentation primitives

| Term | Meaning |
| --- | --- |
| **trampoline** | The code stub Frida writes at a hook target to detour calls to the dispatcher. |
| **Interceptor** | The hooking API: `attach`/`replace`/`revert`/`flush`. |
| **Stalker** | Per-thread code tracer that rewrites the instruction stream as it runs. |
| **CModule** | In-process compiled C for fast, inline instrumentation. |
| **NativePointer** | The JS handle for a native address; all memory read/write goes through it. |
| **eternalize** | `Script.eternalize()` — detach the agent's lifetime from the host so it survives disconnect. |

**Interceptor** vs **Stalker** is the key distinction: Interceptor patches a
single call site (cheap, per-call args); Stalker rewrites the whole instruction
stream (heavy, per-instruction). If you only need call arguments, use
Interceptor — reaching for Stalker is the classic "why is my app crawling" bug
(see [runtime-and-trace-noise.md](../troubleshooting/runtime-and-trace-noise.md)).

## The runtimes

| Term | Meaning |
| --- | --- |
| **QJS / V8** | The two JS runtimes; QuickJS is default, V8 is opt-in (`--runtime=v8`). |

QJS is lighter and the tested default; V8 gives you V8-only features. If a
script behaves differently from your expectations and you used an ES feature,
suspect the engine before the API — check `Script.runtime` to confirm which is
active (see [runtime-and-trace-noise.md](../troubleshooting/runtime-and-trace-noise.md)).

## The platform bridges

| Term | Meaning |
| --- | --- |
| **ART** | Android Runtime — the VM executing dex bytecode; the Java bridge talks to it. |
| **dispatch queue** | The GCD queue ObjC code runs on; `ObjC.schedule` targets one. |
| **spawn gating** | Spawn the app paused, install hooks, then resume — so early code is caught. |
| **version skew** | Host `frida` and device `frida-server` being different versions; the top failure cause. |

**spawn gating** is the umbrella term for the `-f` + `--pause` +
`Process.resume()` dance in [spawn-gating.md](../android/spawn-gating.md) /
[../ios/ios-spawn-gating.md](../ios/ios-spawn-gating.md). If the app's early
code runs before your hooks are in, you weren't gating — you were attaching too
late (see [hooks-never-fire.md](../troubleshooting/hooks-never-fire.md)).
