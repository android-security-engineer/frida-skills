---
name: short-circuit-function
description: Frida agent that replaces a native function outright with Interceptor.replace and a NativeCallback so the original body never runs — stub out a function.
---

# Skip a function body entirely (Interceptor.replace)

**When:** you want a function to do *nothing* and return a fixed value — the
original body must never execute (an anti-debug routine, a telemetry uploader, a
delay). `Interceptor.replace` swaps the whole implementation.

```js
// recipe.js — stub out a function so it returns 0 and never runs its body.
const mod = Process.getModuleByName('libapp.so');
const target = mod.getExportByName('anti_debug_check');

// NativeCallback(fn, returnType, argTypes). Signature must match the real one.
const stub = new NativeCallback(function (arg0, arg1) {
  console.log(`anti_debug_check(${arg0}, ${arg1}) -> stubbed, returns 0`);
  return 0;                                // 'int' return → return a JS number
}, 'int', ['pointer', 'int']);

Interceptor.replace(target, stub);
console.log('[+] replaced anti_debug_check()');
```

If you sometimes need the real behavior, keep a callable to the original:

```js
// recipe-passthrough.js — call the original conditionally.
const mod = Process.getModuleByName('libapp.so');
const target = mod.getExportByName('process');
const orig = new NativeFunction(target, 'int', ['pointer']);   // 'int' → JS number

Interceptor.replace(target, new NativeCallback(function (p) {
  if (p.isNull()) return -1;              // short-circuit the null case
  return orig(p);                         // otherwise run the real function
}, 'int', ['pointer']));
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- The `NativeCallback` return/arg types MUST match the real prototype, or you'll
  corrupt the stack. `'int'`/`'uint'` returns are plain JS numbers; `'pointer'`
  returns a NativePointer.
- Undo it later: `Interceptor.revert(target)`.
- Only overriding the return of a function whose body is harmless? The lighter
  [replace-return-value.md](replace-return-value.md) avoids re-implementing the ABI.
- Need the return but not the side effects, and can't stub cleanly? Patch the
  instruction instead — see [patch-instruction.md](patch-instruction.md).
