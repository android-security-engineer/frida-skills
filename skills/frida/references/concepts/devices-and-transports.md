---
name: devices-and-transports
description: Explains Frida device types (local, USB, remote) and transports — the -U and -H flags, device selection in Python, and TCP forwarding — so an agent can reach the right target.
---

# Devices and transports: reaching the right target

Before any hooking, the host must connect to the **device** that holds your target
process. Picking the wrong device is why "process not found" appears when the app
is clearly running — it's running on a device the host isn't looking at.

## What "device" means

frida-core models every reachable Frida endpoint as a *device*:

- **Local** — processes on the same machine as the host. No flag needed.
- **USB** (`-U`) — a phone/tablet reached over USB via `frida-server` or an
  embedded gadget. frida-core handles adb/usbmuxd forwarding for you.
- **Remote** (`-H host:port`) — any `frida-server` reachable over TCP, local or
  across the network.

List everything currently reachable:

```sh
frida-ls-devices
```

An empty or local-only list on a phone means the on-device server/gadget isn't
running or isn't reachable — see [frida-server.md](frida-server.md).

## Selecting a device on the CLI

```sh
frida-ps                       # local processes
frida-ps -U                    # USB device processes
frida-ps -H 127.0.0.1:27042    # remote/forwarded server
frida -U -n com.example.app -l agent.js
frida -H 192.168.1.50:27042 -n target -l agent.js
```

`-U` picks *the* USB device; if several are attached, disambiguate by id with
`-D <device-id>` (get ids from `frida-ls-devices`).

## Selecting a device in Python

```python
import frida
local  = frida.get_local_device()
usb    = frida.get_usb_device()                 # first USB device
remote = frida.get_device_manager().add_remote_device("192.168.1.50:27042")
by_id  = frida.get_device("0123456789ABCDEF")   # exact device id

session = usb.attach("com.example.app")
```

`frida.get_device_manager()` enumerates and manages devices, and lets you add
remote endpoints explicitly. Prefer `get_usb_device()` for phones and
`add_remote_device(...)` for TCP servers.

## Transports and forwarding

- **USB** is not raw USB to Frida — frida-core forwards over adb (Android) or
  usbmuxd (iOS) transparently. If `adb devices` is empty, `-U` will find nothing.
- **TCP** is a plain socket to `frida-server`'s listen address (default
  `127.0.0.1:27042`). To avoid exposing an unauthenticated port on the network,
  forward loopback over adb instead of binding `0.0.0.0`:

```sh
adb forward tcp:27042 tcp:27042
frida-ps -H 127.0.0.1:27042        # goes to the phone's server over the forward
```

See [security-and-authorization.md](security-and-authorization.md) for why an open
server port is risky.

## Diagnosing the wrong-device class of failure

| Symptom | Cause |
| --- | --- |
| Process visible in the app, "not found" via Frida | Queried the wrong device (missing `-U`/`-H`). |
| `frida-ls-devices` shows only "Local" for a phone | Server/gadget down, or adb/usbmuxd not seeing it. |
| Remote connect times out | Wrong port, not forwarded, or firewall. |
| Two phones, wrong one hooked | Ambiguous `-U` — pin with `-D <id>`. |

Once connected, whether you *spawn* or *attach* on that device is a separate
decision: [spawn-attach-gating.md](spawn-attach-gating.md).
