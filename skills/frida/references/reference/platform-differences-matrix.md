---
name: platform-differences-matrix
description: Side-by-side matrix of what Frida supports on each platform — Linux, macOS, Windows, Android, iOS — across server/gadget, runtimes, bridges, and notable limits.
type: summary
---

# Platform differences matrix

What you can and can't do, per platform. "✓" = supported, "✗" = not, "≈" = partial.

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
