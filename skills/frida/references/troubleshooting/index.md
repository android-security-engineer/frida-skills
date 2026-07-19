---
name: troubleshooting-index
description: Index of Frida troubleshooting docs — no device/server, version skew, permission/ptrace errors, hooks not firing, crashes after hook, anti-Frida, stale removed APIs, runtime issues.
---

# Troubleshooting — symptom → cause → fix

Start every diagnosis with `frida-ls-devices` then `frida-ps -U`. Pick the doc
matching your symptom.

| Doc | Symptom |
| --- | --- |
| [no-device-no-server.md](no-device-no-server.md) | "Failed to enumerate processes" / device list empty. |
| [version-skew.md](version-skew.md) | Weird protocol errors — host `frida` vs device `frida-server` mismatch. |
| [abi-mismatch.md](abi-mismatch.md) | Server won't run / crashes — wrong arch (arm64 vs arm vs x86_64). |
| [permission-ptrace.md](permission-ptrace.md) | "unable to access process" / "not permitted" locally. |
| [stale-removed-api.md](stale-removed-api.md) | `TypeError: ... is not a function` — Frida 17 removed the static API you used. |
| [nativefunction-return.md](nativefunction-return.md) | `retval.toInt32 is not a function` — NativeFunction returns a plain number. |
| [hooks-never-fire.md](hooks-never-fire.md) | Hook installed but never triggers (attach-too-late, wrong name, no `Java.perform`). |
| [crash-after-hook.md](crash-after-hook.md) | Target crashes right after the hook lands (bad types, hot path, code cache). |
| [anti-frida-exit.md](anti-frida-exit.md) | App detects Frida (port/maps/threads) and exits. |
| [remote-connect.md](remote-connect.md) | "unable to connect to remote frida-server" over TCP/TLS. |
| [runtime-and-trace-noise.md](runtime-and-trace-noise.md) | QJS vs V8 surprises; frida-trace too slow/noisy. |
