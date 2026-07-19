---
name: spawn-vs-attach
description: Decide between spawning a target with -f (start paused, catch early/startup code) and attaching with -n/-p (hook a running process); explains %resume and startup timing.
---

# Spawn (`-f`) vs attach (`-n`/`-p`)

**When:** every CLI run needs one or the other. The choice decides whether you catch
code that runs *at startup*.

## The rule

| Goal | Use |
| --- | --- |
| Hook code that runs during app launch (init, anti-debug, pinning setup, class load) | **Spawn** with `-f` |
| Hook something in an app that's already running and past startup | **Attach** with `-n` (name) or `-p` (pid) |

## Spawn

```sh
frida -U -f com.example.app -l agent.js
```

`-f` launches the app **paused at entry** and injects your agent before any target
code runs. Nothing executes until you resume:

- In the REPL: type `%resume`.
- `frida-trace`/`frida-discover` resume automatically once handlers are installed.
- To resume immediately in the REPL without typing, that's the default for tools;
  the interactive `frida` REPL waits so you can set up hooks first.

## Attach

```sh
frida -U -n com.example.app -l agent.js     # by name
frida -U -p 4211 -l agent.js                # by pid
```

Attach injects into a live process; the app keeps running. Any code that already ran
(startup checks, one-time init) is **missed**.

## Why it matters

SSL-pinning setup, root/debugger detection, and key derivation often happen once at
launch. Attaching too late means your hooks are installed *after* the event. If a
hook "never fires," suspect this first and switch to `-f`.

## Gotchas

- **Spawned apps start paused** — a "hang" at the prompt is usually a missing
  `%resume`.
- Spawn needs the app's **identifier** (e.g. `com.example.app`), found via
  [frida-ps.md](frida-ps.md) with `-Uai`.
- If you quit before resuming, the app can linger paused — clear it with
  [frida-kill.md](frida-kill.md).
- Gadget-based (non-rooted) targets are effectively "spawn": the app loads the gadget
  itself at launch. See [frida-apk.md](frida-apk.md).
