---
name: frida-ps
description: Use frida-ps to list processes or installed apps on a device with -U/-H, filtering with -a (applications) and -i (include all installed) to find a target's name or pid.
---

# `frida-ps` — list processes and apps

**When:** you need the exact process name, identifier, or pid to feed into `frida`,
`frida-trace`, or `frida-kill`. It's the second diagnostic after
[frida-ls-devices.md](frida-ls-devices.md).

## Canonical command

```sh
frida-ps -U            # processes running on the USB device
```

## Common variants

| Command | Lists |
| --- | --- |
| `frida-ps -U` | Running processes on the USB device. |
| `frida-ps -Ua` | Running **applications** (PID, Name, Identifier). |
| `frida-ps -Uai` | **All installed** apps, running or not (`-i` = include installed). |
| `frida-ps -H 127.0.0.1:27042` | Processes on a remote frida-server over TCP. |
| `frida-ps` | Processes on the **local** machine. |
| `frida-ps -D <id>` | Processes on a specific device id. |

`-a` shows the app/bundle identifier column — that identifier is what you pass to
`-f` (spawn) or `-n` (attach).

## Examples

```sh
frida-ps -Uai                      # find an app's package name to spawn
frida-ps -Ua | grep -i bank        # locate a running app by label
frida-ps -H 192.168.1.50:27042     # enumerate a networked device
```

Typical Android output columns: `PID  Name  Identifier`, e.g.
`4211  Example  com.example.app`. Use `com.example.app` with `-f`/`-n`.

## Gotchas

- **Empty output on mobile ⇒ no reachable server.** Check
  [frida-ls-devices.md](frida-ls-devices.md) and [frida-server-setup.md](frida-server-setup.md).
- `-i` only makes sense with a device that exposes an app list (Android/iOS); on a
  bare Linux target there is no installed-app concept.
- Process names can differ from app labels; prefer the **Identifier** column
  (package/bundle id) for `-f`/`-n` to avoid ambiguity.
- To act on a target once found, see [target-selection.md](target-selection.md).
