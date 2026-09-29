---
name: platform-differences-matrix
description: Side-by-side matrix of what Frida supports on each platform — Linux, macOS, Windows, Android, iOS — across server/gadget, runtimes, bridges, and notable limits.
type: leaf
---

# Platform differences matrix

What you can and can't do, per platform. "✓" = supported, "✗" = not, "≈" = partial.

## Reading the matrix

- **Desktop (`frida`, `frida-ps`, …) works against all five platforms** — the
  matrix is about *where the target runs*, not where your CLI runs. A Linux
  laptop can attach to an Android device over USB and an iPhone over the same
  USB.
- **The bridges define the matrix.** Java (`Java.*`) only exists where an ART
  VM is running (Android); ObjC (`ObjC.*`) only where the Objective-C runtime
  is (macOS, iOS). Don't write a Java hook and expect it on Linux — the global
  simply isn't defined there.
- **"Local" vs "server" host in the first rows is the load-bearing split** —
  if your CLI can't see the target, fix that before any hook:
  [no-device-no-server.md](../troubleshooting/no-device-no-server.md).

| Capability | Linux | macOS | Windows | Android | iOS |
| --- | --- | --- | --- | --- | --- |
| Attach to local process | ✓ | ✓¹ | ✓ | via server | via server |
| Spawn local | ✓ | ✓¹ | ✓ | `-f pkg` | `-f bundle` |
| `frida-server` | ✓ | ✓ | ✓ | ✓ (root) | ✓ (jailbreak) |
| `frida-gadget` embed | ✓ | ✓ | ✓ | ✓ (repack) | ✓ (resign) |
| Java bridge (`Java.*`) | ✗ | ✗ | ✗ | ✓ | ✗ |
| ObjC bridge (`ObjC.*`) | ✗ | ✓ | ✗ | ✗ | ✓ |
| Default runtime | QJS | QJS | QJS | QJS | QJS |
| `--runtime=v8` | ✓ | ✓ | ✓ | ✓ | ≈² |
| Code signing concerns | ✗ | SIP³ | ✗ | ✗ | ✓⁴ |
| Transport | local | local | local | USB | USB |

¹ macOS SIP-protected/system binaries can't be attached without disabling SIP or codesigning with `get-task-allow`.
² V8 may bloat; QJS preferred on mobile.
³ See [../troubleshooting/permission-ptrace.md](../troubleshooting/permission-ptrace.md).
⁴ iOS requires re-signed gadget; see [../ios/gadget-ios.md](../ios/gadget-ios.md).

## Quick start per platform

**Android (rooted emulator/device):**
Install the matching-ABI `frida-server`, forward, then:

```sh
adb push frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell "/data/local/tmp/frida-server &"     # default port 27042
frida-ls-devices                                # -U should now show the device
frida -U -n com.example.app -l hook.js
```

**iOS (jailbroken or re-signed gadget):** no server on a jailbroken device —
connect over SSH with `-H`:
`frida -H 192.168.1.20:22 -n SpringBoard -l hook.js` (see
[gadget-ios.md](../ios/gadget-ios.md) for the resign path).

**Linux / macOS (local process):**
```sh
frida -n some-process -l hook.js     # attach by name (stable, human-readable)
frida -p 1234 -l hook.js              # or by pid (usable only for the exact run)
```
Prefer name where you can — PIDs are reused; names survive restarts.

**Windows:** same as desktop Linux; watch for the
[permission-ptrace.md](../troubleshooting/permission-ptrace.md) edge (SIP on
macOS, and a 64-bit server for 64-bit processes on Windows).

## Notes

- Uptime-critical facts (which runtime is default, `--runtime=v8` availability)
  change between Frida majors — the values here are verified against 17.15.3 and
  re-checked when a script misbehaves on a platform it "should" support.
- Prefer gadget over server when you control the app build (repack/resign): it
  removes the "server not running / wrong ABI" class of problems entirely.
