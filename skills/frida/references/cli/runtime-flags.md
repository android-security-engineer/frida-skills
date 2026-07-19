---
name: runtime-flags
description: Control the Frida JS engine and diagnostics from the CLI — --runtime=qjs|v8 to switch engines, --debug to enable the V8 inspector, and crash-handling flags.
---

# Runtime and diagnostic flags

**When:** you need V8-specific behavior, a debugger, or control over how crashes are
reported. These flags apply to `frida` and most CLI tools.

## Runtime selection

```sh
frida -U -n com.example.app -l agent.js --runtime=v8
```

| Value | Engine |
| --- | --- |
| `--runtime=qjs` | **QuickJS** — the default. Small, fast to inject. |
| `--runtime=v8` | V8 — full ES support, `--debug` inspector, heavier. |

The default is QuickJS. Switch to V8 only when you need its features (e.g. the
inspector or a language feature QJS lacks). In the agent, `Script.runtime` reports
which engine is active.

## Debugging the agent

```sh
frida -U -n com.example.app -l agent.js --runtime=v8 --debug
```

`--debug` enables the V8 inspector so you can attach Chrome DevTools / a Node
inspector to step through agent JS. Requires the V8 runtime.

## Crash handling

| Flag | Effect |
| --- | --- |
| `--squelch-crash` | Suppress Frida's crash-report dump on target crash. |

Useful in batch runs where a target is expected to crash and you don't want the
report noise. See [batch-mode.md](batch-mode.md).

## Examples

```sh
frida -U -f com.example.app -l agent.js --runtime=v8            # need V8 features
frida -U -n com.example.app -l agent.js --runtime=v8 --debug    # step through JS
frida -U -f com.example.app -l agent.js --squelch-crash -q      # tolerate crashes
```

## Gotchas

- `--debug` only works under `--runtime=v8`; it's a no-op / error on QJS.
- V8 has a larger memory and injection footprint — prefer QJS unless you need V8.
- Runtime choice doesn't change the API surface (Interceptor, Module, etc.); it
  changes the JS engine executing your agent.
- These are host-side flags; the agent JS is identical regardless of engine, with
  minor language-feature differences.
