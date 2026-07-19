---
name: no-device-no-server
description: Fixes "Failed to enumerate processes" or an empty device list when frida-ls-devices shows no USB device — frida-server not running, adb down, or wrong connection flag.
---

# No device / no server

## Symptom

- `frida-ls-devices` shows only `local` (no `usb`/remote entry).
- `frida-ps -U` fails with `Failed to enumerate processes: unable to find device`
  or `unable to connect to remote frida-server`.
- Any `-U` command errors before your agent ever loads.

## Cause

The host cannot reach an instrumentation endpoint on the target:

- On Android/iOS, `frida-server` is not running (or was killed on reboot).
- USB transport is down: `adb` doesn't see the phone, or the device is not
  authorized / not in the right mode.
- You used the wrong flag: `-U` (USB) vs `-H host:port` (network) vs local.

## Fix

First, confirm what the host can see, then bring the endpoint up.

```sh
frida-ls-devices          # what transports/devices exist?
frida-ps -U               # can we enumerate the USB device's processes?
```

**Android** — verify adb, then start `frida-server` as root on the device:

```sh
adb devices                                   # must list a "device" (not "unauthorized")
adb shell "su -c 'ls -l /data/local/tmp/frida-server'"
adb shell "su -c '/data/local/tmp/frida-server &'"   # run detached, as root
frida-ps -U                                   # should now list processes
```

If `adb devices` shows `unauthorized`, accept the RSA prompt on the phone. If it
shows nothing, fix the cable/driver or run `adb kill-server && adb start-server`.

**iOS (jailbroken)** — install the Frida package from Cydia/Sileo so the
`frida-server` launch daemon runs, then:

```sh
frida-ps -U
```

**Local process (no device at all)** — drop `-U` entirely:

```sh
frida-ps                  # local processes
frida -p 1234 -l agent.js # attach to a local PID
```

## Still empty?

- Server started but list is empty ⇒ it is likely the **wrong ABI** (crashes on
  launch): see [abi-mismatch.md](abi-mismatch.md).
- Server runs but every command errors oddly ⇒ **version skew** between host
  `frida` and device `frida-server`: see [version-skew.md](version-skew.md).
- "unable to access process" once you can enumerate ⇒
  [permission-ptrace.md](permission-ptrace.md).
- Connecting over TCP instead of USB ⇒ [remote-connect.md](remote-connect.md).
