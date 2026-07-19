---
name: frida-repl
description: Use the interactive frida REPL to attach or spawn a target, load an agent with -l, and drive it live with %load, %resume, %reload and .exit meta-commands.
---

# The `frida` REPL

**When:** you want an interactive JavaScript console *inside* a target — try hooks
live, poke at memory, iterate on an agent without re-launching. This is the default
`frida` command with no batch flags.

## Canonical command

```sh
frida -U -f com.example.app -l agent.js        # spawn app, load agent, drop to REPL
```

`-U` selects the USB device, `-f` spawns the package (paused at entry until you
`%resume`), `-l` loads your agent before the prompt appears.

## Attaching to something already running

```sh
frida -U -n com.example.app          # attach by process name
frida -U -p 1337                     # attach by pid
frida -H 127.0.0.1:27042 -n Twitter  # attach over TCP to a remote frida-server
```

See [target-selection.md](target-selection.md) and [device-selection.md](device-selection.md).

## Meta-commands (typed at the `[…]->` prompt)

| Command | Effect |
| --- | --- |
| `%load agent.js` | Load (or re-load) a script file into the session. |
| `%reload` | Reload every script passed with `-l` from disk. |
| `%resume` | Resume a process that was spawned with `-f` (starts paused). |
| `%unload` | Unload the current REPL script. |
| `%exec file.js` | Execute a file's contents in the REPL context. |
| `.exit` or Ctrl-D | Detach and quit. |

Any other line is evaluated as JavaScript in the agent, so you can inspect live:

```js
Process.arch                                  // 'arm64'
Process.getModuleByName('libc.so').base       // NativePointer
Process.getModuleByName('libssl.so').getExportByName('SSL_read')
```

## Typical spawn-and-iterate loop

```sh
frida -U -f com.example.app -l agent.js
# prompt appears; app is paused
[Pixel::com.example.app]-> %resume       # let it start
# ...edit agent.js in your editor...
[Pixel::com.example.app]-> %reload       # re-inject the edited file
```

## Gotchas

- **Spawned targets start paused.** Nothing runs until `%resume`. Forgetting this
  looks like a hang. See [spawn-vs-attach.md](spawn-vs-attach.md).
- Use `Process.getModuleByName(...).getExportByName(...)`, **not** the removed
  static `Module.getExportByName()` (gone in Frida 17).
- The REPL default runtime is QuickJS. Add `--runtime=v8` if you need V8 features.
  See [runtime-flags.md](runtime-flags.md).
- The REPL is line-oriented; for multi-file or TypeScript agents, bundle with
  [frida-compile.md](frida-compile.md) and load the single output with `-l`.
- For non-interactive runs (CI, one-shot dumps) use `-q`; see [batch-mode.md](batch-mode.md).
