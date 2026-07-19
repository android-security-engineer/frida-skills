---
name: abi-mismatch
description: Fixes frida-server that won't start, exits immediately, or gives "not executable"/"No such file or directory" because its ABI (arm64 vs arm vs x86_64) does not match the device CPU.
---

# ABI mismatch (wrong frida-server architecture)

## Symptom

- `frida-server` exits instantly with no output; `frida-ps -U` then shows an empty
  device list.
- Running it by hand prints `not executable: 64-bit ELF ...`, `No such file or
  directory` (the classic wrong-arch message), or `Exec format error`.
- It worked on one phone, fails on another.

## Cause

`frida-server` binaries are architecture-specific. An `arm64` server won't run on
an `arm` (32-bit) device, an `x86_64` server won't run on an ARM emulator image,
etc. The binary launches and dies before it can open a listening port.

## Fix

Read the device's real ABI, then push the matching server build.

```sh
adb shell getprop ro.product.cpu.abi         # e.g. arm64-v8a, armeabi-v7a, x86_64
```

Map the ABI to the Frida release asset name:

| `ro.product.cpu.abi` | frida-server asset suffix |
| --- | --- |
| `arm64-v8a` | `android-arm64` |
| `armeabi-v7a` | `android-arm` |
| `x86_64` | `android-x86_64` |
| `x86` | `android-x86` |

Download that build **at your host's exact version** (see
[version-skew.md](version-skew.md)) and install it:

```sh
frida --version                              # e.g. 17.15.3
# from https://github.com/frida/frida/releases  pick frida-server-17.15.3-<suffix>.xz
unxz frida-server-17.15.3-android-arm64.xz
adb push frida-server-17.15.3-android-arm64 /data/local/tmp/frida-server
adb shell "su -c 'chmod 755 /data/local/tmp/frida-server'"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

## Verify

Confirm it stays up and reports itself:

```sh
adb shell "su -c '/data/local/tmp/frida-server --version'"   # must print, not error
frida-ps -U                                                  # non-empty list
```

## Notes

- Some 64-bit devices run 32-bit apps. Match the server to the **device**, not the
  app; Frida bridges the app's own bitness.
- Emulators are commonly `x86_64` even though production phones are `arm64` — a
  frequent cause of this on CI.
- Still empty after fixing arch? Check [version-skew.md](version-skew.md) and
  [no-device-no-server.md](no-device-no-server.md).
