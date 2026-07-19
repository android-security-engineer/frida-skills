---
name: frida
description: >-
  Use Frida, the dynamic instrumentation toolkit, to hook, trace, inspect, and
  modify running native or mobile apps at runtime. Trigger when the user wants to
  hook or trace function/method calls, intercept or patch a running process,
  bypass a runtime check (SSL pinning, root/jailbreak/debugger detection), dump
  arguments or memory, spawn an app under instrumentation, write a Frida
  JavaScript agent, or drive the frida / frida-trace CLIs (Android, iOS, Linux,
  macOS, Windows). Covers Frida 16/17 APIs.
---

# Frida: dynamic instrumentation

Frida injects a small JavaScript engine into a target process. Your JS ("the
**agent**") runs *inside* that process with full access to its memory, functions,
and — on mobile — its Java/Objective-C runtimes. The **host** side (a CLI, the
Python/Node bindings, or an MCP client) loads the agent and exchanges messages
with it.

```
  host (frida CLI / python / node / MCP)  ⇄  agent (your JS, inside the target)
        loads script, receives send()          hooks & reads the process
```

Almost every task reduces to: **pick a target → inject an agent that hooks
something → observe or modify what it sees.**

## Before you start: can you reach the target?

| Target | Requirement |
| --- | --- |
| Local process (Linux/macOS/Windows) | Nothing extra; may need `sudo`/ptrace perms. |
| Android | `frida-server` running as root, **or** an APK embedding `frida-gadget`. Connect `-U`. |
| iOS | `frida-server` via jailbreak, **or** a re-signed `frida-gadget`. Connect `-U`. |
| Remote | `frida-server` reachable over TCP; connect `-H host:port`. |

`frida-ls-devices` lists what's reachable. Empty on mobile ⇒ server not running.

## Decision routing — load only what the task needs

This file is the map. Each area has an **`index.md`** that lists its documents;
open the area index, then the specific doc. That two-step keeps context small —
the essence of progressive disclosure.

| The task is about… | Start at |
| --- | --- |
| How Frida works — architecture, injection, server/gadget, protocols | [`references/concepts/index.md`](references/concepts/index.md) |
| Agent JS API — Interceptor, NativeFunction, Memory, Module, Stalker, rpc… | [`references/core-api/index.md`](references/core-api/index.md) |
| Running the CLIs — `frida`, `frida-trace`, `frida-ps`, spawn vs attach… | [`references/cli/index.md`](references/cli/index.md) |
| Android / Java — hooking, spawn gating, pinning & root-detection bypass | [`references/android/index.md`](references/android/index.md) |
| iOS / Objective-C — method hooks, jailbreak-detection bypass, gadget | [`references/ios/index.md`](references/ios/index.md) |
| Copy-paste working scripts for a concrete goal | [`references/recipes/index.md`](references/recipes/index.md) |
| End-to-end workflows & host-side scripting (Python/Node/TypeScript) | [`references/guides/index.md`](references/guides/index.md) |
| Walk-through playbooks for a complete engagement (recon → hook → verify) | [`references/playbooks/index.md`](references/playbooks/index.md) |
| Reference tables — platform matrix, API changes, env globals, glossary | [`references/reference/index.md`](references/reference/index.md) |
| Something fails (no server, arch mismatch, timing, anti-debug, stale API) | [`references/troubleshooting/index.md`](references/troubleshooting/index.md) |

## Three ways in (minimal examples)

**1. Trace calls with zero code** — fastest recon:

```sh
frida-trace -U -n com.example.app -i "*open*" -i "SSL_read"     # native, by name
frida-trace -U -f com.example.app -j "com.example.*!*"          # Android Java methods
```

**2. Inject a script from the CLI:**

```sh
frida -U -f com.example.app -l agent.js            # spawn app, load agent, interactive
frida -U -n Twitter -l agent.js -q                 # attach by name, run, quit (batch)
```

**3. Drive from Python:**

```python
import frida, sys
session = frida.get_usb_device().attach("com.example.app")
script = session.create_script(open("agent.js").read())
script.on("message", lambda msg, data: print(msg))
script.load()
sys.stdin.read()
```

## Conventions that bite (Frida 16/17)

- **This is Frida ≥16 API.** `Module.getExportByName()` / `Module.findExportByName()`
  static helpers were **removed in Frida 17**. Use
  `Process.getModuleByName('libc.so.6').getExportByName('open')` or
  `Module.getGlobalExportByName('open')`.
- **Read/write via the pointer:** `ptr.readUtf8String()`, `ptr.writeInt(0)`,
  `hexdump(ptr, {length: 64})` — not `Memory.read*(ptr)`.
- **Default runtime is QuickJS (QJS)**, not V8 (`--runtime=v8` to switch).
- **Java/ObjC only exist on-device.** Guard with `Java.available` / `ObjC.available`.
- **`send()` is async, one-way;** use `rpc.exports` for host→agent calls returning
  values. See [`references/core-api/index.md`](references/core-api/index.md).

## Authorization

Frida is for instrumenting software **you are authorized to analyze** — your own
apps, engagements with permission, CTFs, research. Confirm the user has that
authority before helping defeat a protection (pinning, root/jailbreak/debugger
detection, license checks).

---

*Maintainers/agents extending this skill: read [`AUTHORING.md`](AUTHORING.md) first —
it holds the verified Frida 17 API facts and house style every doc must follow.*
