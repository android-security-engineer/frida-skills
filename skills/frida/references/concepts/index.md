---
name: concepts-index
description: Index of Frida concept docs — architecture, injection model, frida-server vs gadget, host/agent split, message protocol, runtimes, devices, spawn gating, memory model, security.
---

# Concepts — how Frida actually works

Read these when a task fails for *structural* reasons (can't reach the device,
hook lands too late, wrong runtime) rather than a coding mistake. Start with
`architecture.md`, then jump to the specific piece.

| Doc | Covers |
| --- | --- |
| [architecture.md](architecture.md) | The big picture: Gum, GumJS, the injected agent, the host bindings. |
| [injection-model.md](injection-model.md) | How Frida gets its engine into a process (ptrace, dlopen, thread hijack). |
| [frida-server.md](frida-server.md) | The on-device daemon: install, ABI/version match, ports, rooted vs not. |
| [frida-gadget.md](frida-gadget.md) | The embeddable shared library for non-rooted/re-signed apps; config modes. |
| [host-vs-agent.md](host-vs-agent.md) | What runs where, what each side can and cannot do, why it matters. |
| [message-protocol.md](message-protocol.md) | `send`/`recv`, message shapes, `error` messages, binary payloads. |
| [runtimes-qjs-v8.md](runtimes-qjs-v8.md) | QuickJS (default) vs V8: differences, when to switch, `Script.runtime`. |
| [devices-and-transports.md](devices-and-transports.md) | USB/local/remote devices, `-U`/`-H`, `get_device_manager`, TCP forwarding. |
| [spawn-attach-gating.md](spawn-attach-gating.md) | Spawn vs attach, why early hooks need spawn gating, `resume()`. |
| [memory-model.md](memory-model.md) | Process address space, modules, ranges, protections, pointers as handles. |
| [security-and-authorization.md](security-and-authorization.md) | Legitimate use, authorization, what Frida can/can't hide, anti-Frida basics. |
| [agent-lifecycle-deepdive.md](agent-lifecycle-deepdive.md) | Agent 加载→就绪→卸载全生命周期，含 eternalize 与异常退出语义。 |
| [transport-internals.md](transport-internals.md) | USB/TCP 传输层内部：握手、消息分帧、断线与重连。 |
