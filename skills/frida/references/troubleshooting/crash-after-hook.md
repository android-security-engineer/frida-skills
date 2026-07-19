---
name: crash-after-hook
description: Fixes a target that crashes (SIGSEGV/SIGABRT) right after a hook lands — wrong NativeFunction/NativeCallback types, forgetting to call the original, hot-path overhead, or self-modifying/JITed code.
---

# Crash right after a hook lands

## Symptom

The hook installs and may even log once, then the target dies:
`SIGSEGV`, `SIGABRT`, `Process terminated`, or the app force-closes the instant the
hooked function runs.

## Cause & Fix

Always confirm the session first:

```sh
frida-ls-devices && frida-ps -U
```

### 1. Wrong argument/return types

A mismatched `NativeFunction` / `NativeCallback` signature corrupts the stack or
registers. Match the real C prototype exactly:

```js
// int open(const char *path, int flags, ... )
const openPtr = Process.getModuleByName('libc.so.6').getExportByName('open');
const open = new NativeFunction(openPtr, 'int', ['pointer', 'int']);   // correct types
```

For `Interceptor.replace`, the `NativeCallback` return/arg types must mirror the
original, and you must return a value the caller expects.

### 2. Replaced the function but never called the original

`Interceptor.replace` fully substitutes the function; if the app needs its real
effect, call through:

```js
const targetPtr = Process.getModuleByName('libapp.so').getExportByName('validate');
const orig = new NativeFunction(targetPtr, 'int', ['pointer']);
Interceptor.replace(targetPtr, new NativeCallback(function (ctx) {
  const r = orig(ctx);            // preserve original behavior
  console.log('validate ->', r);
  return r;                       // return a valid 'int'
}, 'int', ['pointer']));
```

Prefer `Interceptor.attach` (observe without replacing) unless you must change
behavior — it's far less crash-prone.

### 3. Hot-path / re-entrancy overhead

Hooking a function called millions of times (memcpy, malloc, per-frame code) can
starve the app or re-enter itself. Filter tightly and do minimal work in the
callback:

```js
Interceptor.attach(Process.getModuleByName('libc.so.6').getExportByName('memcpy'), {
  onEnter(args) {
    if (args[2].toInt32() > 0x10000) {      // only the big copies
      console.log('memcpy', args[2].toInt32());
    }
  }
});
```

Avoid `send()` on every call in a hot path; batch or sample instead.

### 4. Self-modifying / JITed / signed code

Hooking code that is later overwritten, JIT-recompiled, or integrity-checked can
crash. Attach to a stable higher-level API instead, or reapply after the code
region settles. On code you patch, respect memory protections via
`Memory.protect(ptr, size, 'rwx')` and `Memory.patchCode`.

## Notes

- Reproduce with a single, narrow hook to isolate which one crashes.
- If the crash is really the app *detecting* Frida and calling `abort`, see
  [anti-frida-exit.md](anti-frida-exit.md).
