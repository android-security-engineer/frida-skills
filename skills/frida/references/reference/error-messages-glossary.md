---
name: error-messages-glossary
description: Frida runtime and CLI error strings mapped to root cause and the troubleshooting doc that fixes each, so an agent can go from error text to fix in one jump.
type: leaf
---

# Error messages glossary

See the error → jump to the fix. The table maps the exact error text (or a
fragment you'll recognize in the terminal) to the most likely root cause and
the troubleshooting leaf that walks through the fix.

## Fast diagnostic order

Before hunting specifics, run this cheap 5-second triage. It clears the top
three causes (device, version, permissions) that masquerade as everything else:

```sh
frida-ls-devices                # 1. is the host seeing any device?
frida-version                   # 2. host version (compare against server below)
adb shell frida-server --version   # 3. device server version (or via ssh on desktop)
```

If the host and device disagree on version, fix [version-skew.md](../troubleshooting/version-skew.md)
first — nothing else will work until they match.

## Error → fix table

| Error text (or fragment) | Root cause | Fix doc |
| --- | --- | --- |
| `Failed to enumerate processes` | server not running / wrong ABI / version | [../troubleshooting/no-device-no-server.md](../troubleshooting/no-device-no-server.md) |
| `unable to access process with pid N` / `not permitted` | ptrace scope / perms | [../troubleshooting/permission-ptrace.md](../troubleshooting/permission-ptrace.md) |
| `TypeError: Module.getExportByName is not a function` | Frida 17 removed static helper | [../troubleshooting/stale-removed-api.md](../troubleshooting/stale-removed-api.md) |
| `TypeError: ... toInt32 is not a function` | NativeFunction `'int'` return is a plain number | [../troubleshooting/nativefunction-return.md](../troubleshooting/nativefunction-return.md) |
| `unable to connect to remote frida-server` | firewall / binding / TLS | [../troubleshooting/remote-connect.md](../troubleshooting/remote-connect.md) |
| (silent) hooks never fire | attach-too-late / wrong name / no `Java.perform` | [../troubleshooting/hooks-never-fire.md](../troubleshooting/hooks-never-fire.md) |
| (silent) app exits right after hook | anti-Frida detection | [../troubleshooting/anti-frida-exit.md](../troubleshooting/anti-frida-exit.md) |
| (crash) right after hook | bad arg types / hot path / code cache | [../troubleshooting/crash-after-hook.md](../troubleshooting/crash-after-hook.md) |
| weird protocol/handshake error | host vs server version skew | [../troubleshooting/version-skew.md](../troubleshooting/version-skew.md) |
| server binary won't start on device | ABI mismatch (arm64/arm/x86_64) | [../troubleshooting/abi-mismatch.md](../troubleshooting/abi-mismatch.md) |

## The two TypeErrors that fool people

17-era scripts trigger two nearly-identical messages that are *not* the same bug:

| Message | Means | Not |
| --- | --- | --- |
| `Module.getExportByName is not a function` | removed static helper | wrong module name |
| `toInt32 is not a function` | `'int'` return is a plain number | wrong pointer arithmetic |

Each has a dedicated troubleshooting leaf
([stale-removed-api.md](../troubleshooting/stale-removed-api.md),
[nativefunction-return.md](../troubleshooting/nativefunction-return.md)). The
quick tell: if the receiver of `.toInt32()` is `retval` **inside
`Interceptor.onLeave`**, that one is still a `NativePointer` and the message
points to something else — reread the stack line and check which variable is a
native return vs. a script value.

## Reading the fix docs

Each fix doc is ordered *symptom → cause → fix → verify*. Work through it in
that order, and re-run the **exact failing command** after each step — the
glossary row tells you the likely cause, not the verified one; only a clean
re-run of the original command proves the fix (see
[hooks-never-fire.md](../troubleshooting/hooks-never-fire.md) for the
"install clean but never fires" trap).
