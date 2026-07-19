---
name: security-and-authorization
description: Explains legitimate authorized use of Frida, what it can and cannot hide, and anti-Frida detection basics, so an agent reasons responsibly about instrumentation and its limits.
---

# Security, authorization, and detectability

Frida is a powerful instrumentation tool: inside a target it can read and rewrite
memory, replace functions, and defeat runtime checks. That power comes with a
responsibility line and some hard technical limits worth understanding.

## Authorization (read this first)

Frida is for instrumenting software **you are authorized to analyze** — your own
apps, engagements you have written permission for, CTFs, and research. Before
helping defeat a protection (SSL/TLS pinning, root/jailbreak/debugger detection,
license or integrity checks), confirm the user has that authority. Note this in
any doc or script whose purpose is to bypass a protection.

This is not a legal formality tacked on — instrumenting or modifying software you
don't own or lack permission to test can violate terms of service, computer-misuse
law, and platform rules. Scope your work to targets you control or are cleared to
touch.

## Frida changes the target — that is observable

Injection and hooking are not invisible. A hardened app can detect them. An agent
should assume a determined target *can* notice Frida and plan accordingly (or, for
authorized testing, expect to also bypass the detection). Common signals a target
may check:

- **The default server port** — `frida-server` listens on `27042` by default; a
  process can probe `127.0.0.1:27042`. Running on a non-default port or forwarding
  over adb loopback reduces this signal (see
  [devices-and-transports.md](devices-and-transports.md)).
- **Named artifacts** — strings/threads/pipes historically associated with Frida
  (e.g. a `frida` thread name, gadget library names, `/data/local/tmp/frida-server`).
- **Injected/`rwx` memory regions** — anti-tamper code scans its own maps for
  unexpected executable or written regions; hooks alter prologues, which integrity
  checks can hash and compare.
- **Ptrace state** — a process can `ptrace(PTRACE_TRACEME)` itself so nothing else
  can attach, or check whether it is already being traced
  ([injection-model.md](injection-model.md)).

You can enumerate your own footprint from the agent to reason about exposure:

```js
// what an anti-tamper routine might scan for
Process.enumerateRanges('rwx').forEach(r =>
  console.log('rwx region', r.base, r.size));
console.log('current thread', Process.getCurrentThreadId());
```

## What Frida can and cannot hide

- **Can:** neutralize a *specific* detection routine by hooking it and returning a
  benign result — e.g. make a "is Frida present?" function always return false.
  This is targeted and requires knowing the check.
- **Cannot:** be globally undetectable by default. There is no switch that hides
  all artifacts; every evasion is another hook against a concrete check. It's an
  arms race, not a setting.

For authorized bypass work, the pattern is always the same: find the detection
function, hook it, and force the outcome you want. The Android/iOS reference docs
cover concrete pinning and root/jailbreak/debugger bypasses; those docs restate
this authorization line because their whole purpose is defeating a protection.

## Blast radius: you are running with the target's privileges

The agent runs **inside** the target with its full access
([host-vs-agent.md](host-vs-agent.md)). A wrong `writeInt` crashes the process; a
bad hook can corrupt state or leak sensitive data over `send()`. Treat every write
as load-bearing, prefer read-only inspection until you understand the target, and
never exfiltrate more than the task requires.

## Practical guidance for an agent

- State the authorization assumption when a task is about bypassing a protection.
- Minimize footprint when stealth matters: non-default ports, loopback forwarding,
  fewer/`rwx` allocations, `Interceptor.revert` when done.
- Prefer the least invasive approach that answers the question — observe before you
  modify ([memory-model.md](memory-model.md)).
