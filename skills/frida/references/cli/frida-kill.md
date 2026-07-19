---
name: frida-kill
description: Use frida-kill to terminate a target process on a device by pid or name, cleaning up a spawned or stuck app between instrumentation runs.
---

# `frida-kill` — terminate a target

**When:** an app is stuck (e.g. left paused after a spawn), or you want a clean slate
before re-running. `frida-kill` kills a process on the selected device.

## Canonical command

```sh
frida-kill -U com.example.app        # kill by name/identifier on the USB device
```

You can also kill by pid:

```sh
frida-kill -U 4211
```

## Common options

| Flag | Meaning |
| --- | --- |
| `-U` | Use the USB device. |
| `-H host:port` | Use a remote frida-server over TCP. |
| `-D <id>` | Select a specific device id. |

The final argument is the target: an app identifier / process name, or a numeric pid.

## Examples

```sh
frida-ps -Ua                          # find the pid/name
frida-kill -U com.example.app         # kill it
frida-kill -H 127.0.0.1:27042 4211    # kill pid on a remote server
```

## Gotchas

- A process **spawned with `-f` starts paused**; if you quit `frida` before resuming,
  the app may linger. `frida-kill` clears it. See [spawn-vs-attach.md](spawn-vs-attach.md).
- On Android, the OS may immediately restart a killed foreground app — that's normal.
- Killing requires the same reachable `frida-server`/device as launching did; verify
  with [frida-ls-devices.md](frida-ls-devices.md) first.
- Find the exact name/pid with [frida-ps.md](frida-ps.md) to avoid killing the wrong
  target.
