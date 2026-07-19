---
name: target-selection
description: Choose the target on a device — -f program to spawn, -n name or -p pid to attach to a running process; explains identifiers vs names and when each flag applies.
---

# Selecting the target process

**When:** after picking a device ([device-selection.md](device-selection.md)), you
must name *what* to instrument. These flags are shared by `frida`, `frida-trace`,
`frida-discover`, and friends.

## The flags

| Flag | Target |
| --- | --- |
| `-f PROGRAM` | **Spawn** this program/app identifier (starts paused). |
| `-n NAME` | **Attach** to a running process by name. |
| `-p PID` | **Attach** to a running process by numeric pid. |

Spawn vs attach semantics — and why startup timing matters — are covered in
[spawn-vs-attach.md](spawn-vs-attach.md).

## Examples

```sh
frida -U -f com.example.app -l agent.js     # spawn Android app by package id
frida -U -n com.example.app -l agent.js     # attach to the running app
frida -U -p 4211 -l agent.js                # attach by pid
frida -n Firefox -l agent.js                # local process by name
```

## Names vs identifiers

- On Android/iOS, `-f` wants the **package/bundle identifier** (`com.example.app`),
  which you get from `frida-ps -Uai` (Identifier column).
- `-n` matches the **process name**, which for many mobile apps equals the identifier
  but can differ (e.g. a display label). Prefer the identifier to be unambiguous.
- `-p` is exact and never ambiguous — use it when several processes share a name.

## Finding the value

```sh
frida-ps -Uai            # installed apps: PID, Name, Identifier
frida-ps -Ua             # running apps only
```

See [frida-ps.md](frida-ps.md).

## Gotchas

- `-f`, `-n`, and `-p` are mutually exclusive — pick exactly one.
- A name that matches **multiple** processes errors out; switch to `-p PID`.
- Spawning (`-f`) an app that's already running launches a fresh, paused instance;
  kill the old one with [frida-kill.md](frida-kill.md) if it interferes.
- Attaching requires the process to already exist; for startup code, spawn instead.
