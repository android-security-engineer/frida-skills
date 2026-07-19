---
name: replace-return-value
description: Frida agent that forces a native function (license/flag/auth check) to return a constant value using retval.replace inside Interceptor.onLeave.
---

# Force a function to return a constant

**When:** a native check function (e.g. `is_licensed`, `verify`, `check_root`)
returns a bool/int you want to override. Hook it and replace the return value.

```js
// recipe.js — force a check function to always return 1 (true)
// Change the module + symbol to your target. Here: a fictional libapp.so export.
const mod = Process.getModuleByName('libapp.so');
const target = mod.getExportByName('is_licensed');   // or use an address: mod.base.add(0x1234)

Interceptor.attach(target, {
  onLeave(retval) {
    // retval is a NativePointer wrapping the return register.
    const original = retval.toInt32();       // int-typed return → .toInt32()
    retval.replace(ptr(1));                   // overwrite with 1 (true)
    console.log(`is_licensed() = ${original} -> 1`);
  },
});
console.log('[+] patched is_licensed()');
```

If you only have an address (no exported symbol), hook by offset instead:

```js
// recipe-offset.js — hook at a fixed offset from the module base
const mod = Process.getModuleByName('libapp.so');
const target = mod.base.add(0x00012a40);      // RVA from your disassembler
Interceptor.attach(target, {
  onLeave(retval) { retval.replace(ptr(0)); }, // force 0 (e.g. "no error")
});
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn (Android/iOS)
frida -n myprocess -l recipe.js               # attach by name (local)
```

**Tweak this:**
- Return a pointer instead of an int? `retval.replace(somePtr)` — any NativePointer.
- Conditional override: read `this.arg0` in `onEnter` (stash `args[0]`) and only
  replace when it matches, so you don't break unrelated call sites.
- Need to also change *arguments* before the body runs? See
  [swap-argument.md](swap-argument.md).
- Want to skip the body entirely (never run the original)? See
  [short-circuit-function.md](short-circuit-function.md).
- For a Java/Kotlin method return, hook the method and `return true;` in the
  `.implementation` instead — see [android-ssl-pinning.md](android-ssl-pinning.md).
