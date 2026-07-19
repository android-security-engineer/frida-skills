---
name: frida-server
description: Explains the on-device frida-server daemon — install, ABI/version matching, ports, and rooted requirements — so an agent can set up and debug USB/remote device access.
---

# frida-server: the on-device daemon

`frida-server` is a standalone binary you run **on the target device**. It listens
for the host, performs injection there (see [injection-model.md](injection-model.md)),
and relays messages. It is the standard way to reach Android and jailbroken iOS
from your machine over USB or TCP.

## The two non-negotiables: privilege and match

1. **Privilege.** The server injects into other processes, so it needs root
   (Android via `su`/`adb root`; iOS via a jailbreak). Without root it can only
   see, not instrument, most processes.
2. **ABI + version match.** The server binary must match the device CPU (`arm64`,
   `arm`, `x86_64`, `x86`) **and** its version must match the host `frida`
   package. Version skew between host and server is the single most common
   failure — always install the server that matches your host `frida` version.

```sh
frida --version          # host version, e.g. 17.15.3
# download frida-server-17.15.3-android-arm64 to match exactly
```

## Install and run (Android example)

```sh
adb push frida-server-17.15.3-android-arm64 /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c /data/local/tmp/frida-server &"     # run as root, backgrounded
```

Verify from the host — an empty list means the server is not actually running or
not reachable:

```sh
frida-ls-devices                 # the USB device should appear
frida-ps -U | head               # lists processes on the device
```

## How the host reaches it

- **USB** (`-U`): frida-core discovers the device (adb/usbmuxd) and forwards to the
  server automatically. This is the default for phones.
- **Remote/TCP** (`-H host:port`): the server listens on `127.0.0.1:27042` by
  default. Expose it and connect over the network:

```sh
# device: bind on all interfaces (or forward a port with adb)
adb shell "su -c '/data/local/tmp/frida-server -l 0.0.0.0:27042 &'"
frida-ps -H 192.168.1.50:27042
# safer alternative — forward the loopback port over adb, no open network port:
adb forward tcp:27042 tcp:27042 && frida-ps -H 127.0.0.1:27042
```

Prefer `adb forward` over binding `0.0.0.0`: an open server port is unauthenticated
by default. See [security-and-authorization.md](security-and-authorization.md).

## Multiple servers / non-default port

Run a second instance on another port and select it by address; useful when two
tools want isolated servers:

```sh
adb shell "su -c '/data/local/tmp/frida-server -l 127.0.0.1:27055 &'"
adb forward tcp:27055 tcp:27055 && frida-ps -H 127.0.0.1:27055
```

## Troubleshooting checklist

| Symptom | Cause / fix |
| --- | --- |
| `frida-ls-devices` shows no USB device | Server not running, or `adb devices` empty. |
| "unable to connect to remote frida-server" | Wrong port, not forwarded, or not root. |
| "unsupported version" / handshake error | Host vs server version skew — match them. |
| Attach fails with EPERM | Server not running as root. |
| Wrong-arch binary won't execute | Pushed the wrong ABI build. |

For non-rooted devices where you cannot run a server at all, embed the engine
instead: [frida-gadget.md](frida-gadget.md). For choosing between `-U` and `-H`,
see [devices-and-transports.md](devices-and-transports.md).
