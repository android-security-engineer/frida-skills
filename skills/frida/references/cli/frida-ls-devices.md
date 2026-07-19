---
name: frida-ls-devices
description: Use frida-ls-devices as the first diagnostic to list every device Frida can reach (USB, local, remote); an empty or missing device means frida-server is not running.
---

# `frida-ls-devices` — what can Frida reach?

**When:** *first*, before anything else, whenever a connection fails or you're unsure
a device is wired up. It answers "is the target reachable at all?"

## Canonical command

```sh
frida-ls-devices
```

Output is a table of `Id  Type  Name`:

```
Id                    Type    Name
--------------------  ------  ------------
local                 local   Local System
0123456789abcdef      usb     Pixel 7
socket                remote  Local Socket
```

## Reading the result

| You see… | Meaning |
| --- | --- |
| A `usb` row with your phone | `frida-server` is running and reachable — use `-U`. |
| Only `local` (no usb row) | Device not connected, or `frida-server` not started. |
| A `remote` row | A TCP-reachable server (use `-H host:port`). |

## Connecting a remote device first

`frida-ls-devices` shows USB and local automatically. For a networked server, target
it directly with `-H` on the other tools:

```sh
frida-ps -H 192.168.1.50:27042
```

## Gotchas

- **No `usb` row on Android/iOS** is the single most common failure. Causes: server
  not started, wrong ABI/arch build, or version skew between host `frida` and device
  `frida-server`. See [frida-server-setup.md](frida-server-setup.md) and the
  troubleshooting index.
- USB access may require `adb` running (Android) and the device authorized/unlocked.
- The **host `frida` and device `frida-server` versions must match** — a mismatch can
  still show the device but fail on attach. Check `frida --version`.
- Once a device appears, list its targets with [frida-ps.md](frida-ps.md).
