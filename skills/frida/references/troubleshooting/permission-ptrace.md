---
name: permission-ptrace
description: Fixes "unable to access process", "operation not permitted", or ptrace failures when attaching locally on Linux/macOS — caused by ptrace_scope, missing root/entitlements, or a hardened target.
---

# Permission / ptrace errors (local attach)

## Symptom

- `Failed to attach: unable to access process with pid N (operation not permitted)`
- `Failed to attach: process is not running or not accessible`
- Local injection fails even though the process clearly exists in `frida-ps`.

## Cause

Frida injects by attaching to the target (ptrace on Linux, task ports on macOS).
The OS blocks that when:

- Linux **Yama** `ptrace_scope` is `1` (restricted) or higher, so a non-parent,
  non-root process cannot ptrace.
- You lack privileges — the target runs as another user or as root.
- macOS SIP / lack of a debugging entitlement, or a hardened runtime target.

## Fix

Diagnose first, as always:

```sh
frida-ls-devices
frida-ps                  # local — can you even see the target?
```

**Linux — check and relax `ptrace_scope`:**

```sh
cat /proc/sys/kernel/yama/ptrace_scope       # 0 = open, 1 = restricted, 2/3 = locked
sudo sysctl -w kernel.yama.ptrace_scope=0    # allow ptrace this boot
```

Then attach. If the target runs as another user or root, run Frida with privilege:

```sh
sudo frida -p 1234 -l agent.js
```

For spawn-based work under sudo:

```sh
sudo frida -f /usr/bin/target-binary -l agent.js
```

**macOS — use sudo, and disable SIP only in a lab if required:**

```sh
sudo frida -p 1234 -l agent.js               # most local attaches just need root
csrutil status                               # if SIP blocks it (run from Recovery to change)
```

## Notes

- On Android these errors usually mean `frida-server` isn't running **as root** —
  restart it with `su`, see [no-device-no-server.md](no-device-no-server.md).
- If attach succeeds but your hook never triggers, that's a different problem:
  [hooks-never-fire.md](hooks-never-fire.md).
- Resetting `ptrace_scope` to `0` lowers a security boundary; do it on machines you
  control and revert with `sysctl -w kernel.yama.ptrace_scope=1` when done.
