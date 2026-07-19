---
name: ios-debugger-detection
description: Bypassing iOS anti-debugging with Frida — neutralizing ptrace(PT_DENY_ATTACH), sysctl P_TRACED checks, and getppid/isatty tricks by replacing or patching the return values.
---

# Bypass iOS debugger / anti-attach detection

**Authorization:** only on software **you are authorized to analyze**. Defeating
anti-debug is a protection bypass.

**When to use:** the app detects instrumentation and exits, or Frida can't attach
because the process called `ptrace(PT_DENY_ATTACH)`. Neutralize the specific
mechanism. Spawn-gate ([ios-spawn-gating.md](ios-spawn-gating.md)) — these checks
usually fire in a constructor or at launch, before an ObjC hook could land, so hook
the native layer early ([ios-native-hooks.md](ios-native-hooks.md)).

## Common mechanisms

| Mechanism | Effect | Bypass |
| --- | --- | --- |
| `ptrace(PT_DENY_ATTACH, …)` | kernel refuses debugger/Frida attach | replace `ptrace` with a no-op |
| `sysctl` `KERN_PROC` → `P_TRACED` flag | detects a tracer, then exits | clear the `P_TRACED` bit in the result |
| `getppid() != 1` | launched by a debugger | force return 1 |
| `isatty`/`_dyld` env checks | detect debug session | patch as needed |

## Shortest working example — neutralize ptrace

```js
const ptrace = Module.getGlobalExportByName('ptrace');
Interceptor.replace(ptrace, new NativeCallback(function (request, pid, addr, data) {
  // PT_DENY_ATTACH = 31: swallow it; pass others through if you like
  return 0;
}, 'int', ['int', 'int', 'pointer', 'pointer']));
```

Because `ptrace` on iOS is often called via `syscall`/`svc` directly, also consider
hooking `syscall` and filtering `SYS_ptrace (26)` if the simple replace doesn't
stick.

## Clearing P_TRACED after sysctl

```js
const sysctl = Module.getGlobalExportByName('sysctl');
Interceptor.attach(sysctl, {
  onEnter(args) { this.oldp = args[2]; },            // struct kinfo_proc*
  onLeave(retval) {
    if (this.oldp.isNull()) return;
    // kinfo_proc.kp_proc.p_flag is at offset 32; P_TRACED = 0x800
    const pFlag = this.oldp.add(32);
    const v = pFlag.readU32();
    if (v & 0x800) pFlag.writeU32(v & ~0x800);       // clear the traced bit
  }
});
```

## getppid check

```js
const getppid = Module.getGlobalExportByName('getppid');
Interceptor.replace(getppid, new NativeCallback(() => 1, 'int', []));
```

## Pitfalls

- **Install before the check runs.** Anti-debug in a `+load`/constructor beats a
  late attach — spawn-gate and hook the native layer first.
- **Offsets are version-specific.** The `p_flag` offset (32) matches common
  `kinfo_proc` layouts but verify with `hexdump(this.oldp, {length:64})` on your
  target before trusting it.
- **Direct syscalls bypass libc.** If replacing `ptrace` has no effect, the app
  used inline `svc #0x80`; hook `syscall` or patch the call site with
  [../core-api/memory-protect-patchcode.md](../core-api/memory-protect-patchcode.md).
- **Multiple layers.** Apps stack several checks; a backtrace at the exit call
  reveals which one you missed.
