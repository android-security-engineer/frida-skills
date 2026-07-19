---
name: error-messages-glossary
description: Frida runtime and CLI error strings mapped to root cause and the troubleshooting doc that fixes each, so an agent can go from error text to fix in one jump.
type: summary
---

# Error messages glossary

See the error → jump to the fix.

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
