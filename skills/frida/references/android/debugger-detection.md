---
name: debugger-detection
description: Defeat Android debugger-detection checks (Debug.isDebuggerConnected, TracerPid in /proc status, native ptrace anti-attach) by hooking the probes, for authorized analysis of apps that abort when traced.
---

# Defeat Android debugger detection

**Authorization:** Frida is for software you are authorized to analyze — your own
apps, permissioned engagements, CTFs, research. Only bypass these checks on apps
you are permitted to test.

**When to use:** the app detects a debugger/tracer and exits, kills threads, or
hides logic. Frida attaching can trip `ptrace`-based anti-debug. These usually run
early, so spawn-gate ([spawn-gating.md](spawn-gating.md)).

## What the check looks for

- Java: `android.os.Debug.isDebuggerConnected()` / `waitingForDebugger()`.
- `TracerPid:` line in `/proc/self/status` (non-zero ⇒ traced).
- Native `ptrace(PTRACE_TRACEME)` returning `-1` (already traced), or a watchdog
  thread re-reading `TracerPid`.

## Shortest working example — lie to isDebuggerConnected

```js
Java.perform(() => {
  const Debug = Java.use('android.os.Debug');
  Debug.isDebuggerConnected.implementation = function () {
    console.log('[dbg] isDebuggerConnected -> false');
    return false;
  };
  Debug.waitingForDebugger.implementation = function () { return false; };
});
```

## Hide TracerPid in /proc/self/status

Apps read `/proc/self/status` and grep `TracerPid`. Rewrite the value on read:

```js
const libc = Process.getModuleByName('libc.so');
const openp = libc.getExportByName('open');
Interceptor.attach(libc.getExportByName('read'), {
  onEnter(args) { this.buf = args[1]; this.count = args[2].toInt32(); },
  onLeave(retval) {
    const n = retval.toInt32();
    if (n <= 0) return;
    let s;
    try { s = this.buf.readUtf8String(n); } catch (e) { return; }
    if (s && s.includes('TracerPid:')) {
      const fixed = s.replace(/TracerPid:\t\d+/,'TracerPid:\t0');
      this.buf.writeUtf8String(fixed);
    }
  }
});
```

Reading through the pointer (`readUtf8String`/`writeUtf8String`) is the required
form — see the memory rules in [../core-api/index.md](../core-api/index.md).

## Neuter native ptrace anti-attach

`ptrace(PTRACE_TRACEME)` fails if a process is already traced; some apps call it
to prevent a debugger, or fork a watchdog that calls it. Make it succeed:

```js
const libc = Process.getModuleByName('libc.so');
const ptrace = libc.findExportByName('ptrace');
if (ptrace) {
  Interceptor.replace(ptrace, new NativeCallback(function () {
    return 0;                                  // pretend success, no real trace
  }, 'long', ['int', 'int', 'pointer', 'pointer']));
}
```

## Pitfalls

- **Watchdog threads.** A single early hook isn't enough if a thread re-checks in a
  loop — hook the check function itself, not just the first call site.
- **Frida-specific anti-debug.** Some checks target Frida directly (thread names,
  ports); pair with [frida-detection.md](frida-detection.md).
- **ptrace signature.** On Android `ptrace` is `long ptrace(int, ...)`; the
  4-arg callback above matches typical usage. Verify args if behavior is odd.
- **Timing.** Spawn-gate so the hooks precede the first probe
  ([spawn-gating.md](spawn-gating.md)).
