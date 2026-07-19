---
name: frida-trace
description: Use frida-trace to trace native C/library functions by name or glob with -i/-x includes and excludes, generating editable per-function handler stubs — zero-code recon.
---

# `frida-trace` — native function tracing

**When:** you want to see *which* native functions run and with what arguments,
without writing an agent. This is the fastest recon tool. For Android Java use
[frida-trace-java.md](frida-trace-java.md); for iOS/macOS Objective-C use
[frida-trace-objc.md](frida-trace-objc.md).

## Canonical command

```sh
frida-trace -U -n com.example.app -i "SSL_read" -i "SSL_write"
```

`-i` (include) takes a function name or glob; each match gets a generated JS
handler that logs the call. `-U` = USB device.

## Common options

| Flag | Meaning |
| --- | --- |
| `-i GLOB` | Include functions matching a glob (repeatable). |
| `-x GLOB` | Exclude functions (repeatable); applied after includes. |
| `-a MODULE!OFFSET` | Trace a raw address/offset in a module. |
| `-I MODULE` | Include all exports of a module. |
| `-X MODULE` | Exclude a whole module. |
| `-f PROGRAM` | Spawn instead of attach (see below). |
| `-o trace.log` | Write trace output to a file. |
| `--decorate` | Append the module name to each traced symbol. |

Globs match export names: `-i "*open*"` traces `open`, `openat`, `fopen`, …

## Spawn vs attach

```sh
frida-trace -U -f com.example.app -i "SSL_read"    # spawn, trace from process start
frida-trace -U -n com.example.app -i "SSL_read"    # attach to running instance
```

Spawn (`-f`) is required to catch calls that happen during startup. `frida-trace`
resumes the spawned process automatically once handlers are installed.

## Editing handlers

Each matched function creates a file under `__handlers__/<module>/<fn>.js`. Edit it
to log arguments; changes hot-reload on the next call:

```js
onEnter(log, args, state) {
  log('SSL_read(fd=' + args[0].toInt32() + ', buf=' + args[1] + ')');
},
onLeave(log, retval, state) {
  log('  => ' + retval.toInt32());
}
```

`args[i]` and `retval` are **NativePointers**; read strings/buffers through them
(e.g. `args[1].readByteArray(retval.toInt32())`).

## Gotchas

- A name with no matches prints nothing and no handler is created — widen the glob
  (`-i "*ssl*"`) or confirm the library is loaded (functions in not-yet-loaded
  modules won't match at start; spawn with `-f` and re-check).
- Quote globs so the shell doesn't expand `*`.
- On a stripped binary only exported symbols match by name; use `-a MODULE!0x1234`
  for non-exported offsets.
- Very broad includes (`-i "*"`) flood output and slow the target; narrow with `-x`.
