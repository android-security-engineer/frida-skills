---
name: runtimes-qjs-v8
description: Explains Frida's two JavaScript runtimes — QuickJS (default) and V8 — their differences, when to switch, and how to check Script.runtime from an agent.
---

# Runtimes: QuickJS vs V8

The agent's JavaScript runs on one of two engines embedded in GumJS. Knowing which
one is active matters for performance, debugging, and the occasional
engine-specific behavior.

## The default is QuickJS (QJS)

Since Frida 16, the default runtime is **QuickJS**, not V8. QJS is small, starts
fast, and has a low memory footprint — ideal for injecting into constrained
targets (mobile apps, small daemons). For the vast majority of hooking and tracing
work, QJS is the right choice and you never need to think about it.

Check which runtime you're on from inside the agent:

```js
console.log('runtime =', Script.runtime);   // 'QJS' or 'V8'
```

## When to switch to V8

V8 is the full engine used by Chrome/Node. Switch to it when you need:

- **Peak throughput** in very hot code paths (e.g. heavy `Stalker` processing or
  tight loops in a busy `Interceptor` callback) — V8's JIT can be faster once warm.
- **A richer debugging experience** — V8 supports the Chrome DevTools inspector
  protocol for step debugging.
- **Certain modern JS features or libraries** that assume V8 semantics.

Trade-offs: V8 uses more memory, starts slower, and is a larger payload to inject —
which can matter on tiny targets or when stealth/footprint is a concern.

## How to select the runtime

From the CLI, pass `--runtime`:

```sh
frida -U -n com.example.app --runtime=v8 -l agent.js
frida -U -n com.example.app --runtime=qjs -l agent.js   # explicit default
```

From the Python bindings, set it when creating the script:

```python
script = session.create_script(open("agent.js").read(), runtime="v8")
```

The runtime is fixed for the life of a script; you cannot switch mid-run.

## Practical implications for an agent

- **Write portable JS.** Both runtimes support modern ECMAScript; avoid depending
  on engine-specific quirks so your agent runs on either.
- **Performance-tune only after measuring.** Reach for V8 when a QJS agent is
  demonstrably CPU-bound, not by default — the smaller QJS footprint is usually a
  net win, especially on mobile.
- **`Script.runtime`** lets an agent branch or log defensively if some behavior
  differs, but well-written Frida code rarely needs to.
- The runtime choice does **not** change the Frida API surface — `Interceptor`,
  `Module`, `Memory`, `NativeFunction` are identical on both. It only changes the
  JS engine executing your code.

## Relation to other layers

The runtime lives inside GumJS in the target process
([architecture.md](architecture.md)); the host frontend merely tells frida-core
which one to instantiate at injection time
([injection-model.md](injection-model.md)). A wrong-runtime choice never blocks
reachability — that's a device/transport concern
([devices-and-transports.md](devices-and-transports.md)) — it only affects speed,
memory, and debuggability inside an already-injected agent.
