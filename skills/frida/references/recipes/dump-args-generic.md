---
name: dump-args-generic
description: Frida agent that logs the first N arguments of any native export with heuristic type guessing (string/pointer/int) — quick blind inspection of an unknown function.
---

# Generic multi-argument logger

**When:** you don't know a function's signature and want a fast look at what it
receives. This prints each of the first N args three ways (as pointer, as int, as
a best-effort C string) so you can eyeball which interpretation is meaningful.

```js
// recipe.js — dump the first N args of an arbitrary export.
const MODULE = 'libc.so.6';   // change to your target module
const SYMBOL = 'strcmp';      // change to the function to inspect
const NARGS  = 4;             // how many args to print

function describe(p) {
  const asInt = p.toInt32();
  let asStr = null;
  try { asStr = p.readUtf8String(64); } catch (_) {}   // may fault; guard it
  const s = (asStr && /^[\x09\x0a\x0d\x20-\x7e]*$/.test(asStr)) ? ` "${asStr}"` : '';
  return `${p}  (int=${asInt})${s}`;
}

const target = Process.getModuleByName(MODULE).getExportByName(SYMBOL);
Interceptor.attach(target, {
  onEnter(args) {
    console.log(`\n[${SYMBOL}]`);
    for (let i = 0; i < NARGS; i++) {
      console.log(`  arg${i} = ${describe(args[i])}`);
    }
  },
  onLeave(retval) {
    console.log(`  ret  = ${retval}  (int=${retval.toInt32()})`);
  },
});
console.log(`[+] hooked ${MODULE}!${SYMBOL}`);
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js
frida -n myprocess -l recipe.js
```

**Tweak this:**
- Reading a string can fault on non-string pointers; the `try/catch` above swallows
  that. Only trust the `"..."` output when the bytes are printable ASCII.
- Bump `NARGS` cautiously — reading past the real arg count reads stack garbage,
  which is harmless to log but meaningless.
- Once you know a real signature, switch to a typed hook —
  see [trace-native-call.md](trace-native-call.md).
- To hook *many* functions matching a pattern at once, use `ApiResolver('module')`
  or the `frida-trace` CLI instead.
