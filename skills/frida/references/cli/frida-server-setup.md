---
name: frida-server-setup
description: Download, push, and run frida-server on a rooted Android or jailbroken iOS device so the host CLIs can reach it over -U; covers ABI matching and version skew.
---

# Setting up `frida-server`

**When:** you have a **rooted Android** or **jailbroken iOS** device and want full
instrumentation (spawn, attach any process). `frida-server` is the on-device daemon
the host CLIs talk to over USB.

## The version rule (read first)

The device `frida-server` version **must match** your host `frida` version. Skew is
the #1 failure. Check the host:

```sh
frida --version        # e.g. 17.15.3 — download the SAME server version
```

## Android (rooted)

Pick the server build matching the device CPU ABI (`arm64`, `arm`, `x86_64`):

```sh
adb shell getprop ro.product.cpu.abi          # e.g. arm64-v8a  -> use android-arm64
# download frida-server-<version>-android-arm64 from the Frida releases, unxz it, then:
adb push frida-server-17.15.3-android-arm64 /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

Verify from the host:

```sh
frida-ls-devices        # a 'usb' row should appear
frida-ps -Uai
```

## iOS (jailbroken)

Install Frida from its Cydia/Sileo repo (`https://build.frida.re`), which runs
`frida-server` automatically, then connect over USB with `-U`. Confirm with
`frida-ls-devices`.

## Remote / networked access

By default the server binds to loopback. To reach it over TCP, either forward:

```sh
adb forward tcp:27042 tcp:27042
frida-ps -H 127.0.0.1:27042
```

or start it listening broadly (trusted networks only):

```sh
adb shell "su -c '/data/local/tmp/frida-server -l 0.0.0.0:27042 &'"
```

See [device-selection.md](device-selection.md).

## Gotchas

- **Wrong ABI** ⇒ server won't start; match `ro.product.cpu.abi` exactly.
- **Version mismatch** ⇒ device may list but attach fails — re-download the matching
  server.
- The server needs **root** to spawn/attach arbitrary apps; without root use a gadget
  instead ([frida-apk.md](frida-apk.md)).
- Exposing `-l 0.0.0.0` is unauthenticated RCE on the device — keep it off untrusted
  networks.
- No `usb` row at all? Diagnose with [frida-ls-devices.md](frida-ls-devices.md).
