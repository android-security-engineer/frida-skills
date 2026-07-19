---
name: frida-discover
description: Use frida-discover to find which functions execute while you perform an action in the target, narrowing a huge binary down to the code paths worth hooking.
---

# `frida-discover` — find functions that run during an action

**When:** you don't know *what* to hook. Run `frida-discover`, perform the action of
interest in the app (log in, tap "Pay", trigger a check), and it reports the
functions that fired — a shortlist to feed into [frida-trace.md](frida-trace.md).

## Canonical command

```sh
frida-discover -U -f com.example.app
```

`-f` spawns the app; drive it manually while discovery samples executing code.
Use `-n com.example.app` to attach to a running instance instead.

## Common options

| Flag | Meaning |
| --- | --- |
| `-f PROGRAM` | Spawn the target and discover from startup. |
| `-n NAME` | Attach to a running process by name. |
| `-p PID` | Attach by pid. |
| `-U` | Use the USB device. |
| `-H host:port` | Use a remote frida-server. |

## Workflow

```sh
frida-discover -U -f com.example.app
# app launches; perform ONLY the action you care about (e.g. tap "Login")
# stop with Ctrl-C; frida-discover prints functions ranked by call count
```

Take the reported module + symbol/offset and trace it:

```sh
frida-trace -U -n com.example.app -a "libnative.so!0x000123ab"
```

## Gotchas

- It works by sampling with Stalker, so it's **heavy** — expect the app to run slowly
  and only exercise the one action you're investigating, to keep the output signal
  high.
- Results are addresses/symbols, not source; on a stripped binary you'll get
  `module!offset` you then trace with `-a` (see [frida-trace.md](frida-trace.md)).
- For Java-level discovery this is the wrong tool — trace Java directly with
  [frida-trace-java.md](frida-trace-java.md) using a package glob.
- Startup-only code needs `-f` (spawn); attaching with `-n` misses it. See
  [spawn-vs-attach.md](spawn-vs-attach.md).
