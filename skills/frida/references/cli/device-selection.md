---
name: device-selection
description: Select which device Frida talks to — -U for USB, -H host:port for a remote frida-server over TCP, -D id for a specific device, or none for the local machine.
---

# Selecting the device

**When:** every Frida CLI command must pick a device. Get this wrong and you hook the
wrong machine (or nothing).

## The flags

| Flag | Selects |
| --- | --- |
| *(none)* | The **local** machine (this computer). |
| `-U` / `--usb` | The USB-attached device (the common case for Android/iOS). |
| `-H host:port` / `--host` | A **remote** frida-server over TCP. |
| `-D id` / `--device id` | A specific device by id (from `frida-ls-devices`). |
| `-R` / `--remote` | The default remote (`127.0.0.1:27042`). |

## Examples

```sh
frida -U -n com.example.app -l agent.js          # phone over USB
frida -H 192.168.1.50:27042 -n com.example.app   # networked frida-server
frida -D 0123456789abcdef -n com.example.app     # pick one of several USB devices
frida -n firefox -l agent.js                     # local process, no device flag
```

## Remote servers (`-H`)

Point `-H` at a `frida-server` listening on TCP. On the device, start it bound to a
port and forward or route to it:

```sh
# on the Android device (as root), listen on all interfaces:
# ./frida-server -l 0.0.0.0:27042
frida-ps -H 192.168.1.50:27042
frida -H 192.168.1.50:27042 -f com.example.app -l agent.js
```

Or forward over adb and use localhost:

```sh
adb forward tcp:27042 tcp:27042
frida-ps -H 127.0.0.1:27042
```

## Gotchas

- With **multiple USB devices**, plain `-U` is ambiguous — use `-D <id>` (get ids
  from [frida-ls-devices.md](frida-ls-devices.md)).
- `-H` requires the server to listen on a reachable interface; the default server
  binds to loopback, so use `-l 0.0.0.0:PORT` or `adb forward`.
- No device flag = local; a common mistake is omitting `-U` and accidentally
  attaching to a host-side process of the same name.
- Exposing `frida-server` on `0.0.0.0` is unauthenticated remote code execution on
  the device — only do it on a trusted network.
