---
name: log-string-functions
description: Frida agent that traces strcmp/strstr/strncmp and open to reveal string comparisons and file paths an app checks at runtime — spot secrets, gates, and probes.
---

# Log string-handling functions

**When:** you want to see what strings an app compares and what files it touches —
a fast way to find hardcoded checks, feature gates, and anti-tamper probes.

```js
// recipe.js — trace a few high-signal libc string/path functions at once.
const libc = Process.getModuleByName('libc.so.6');   // 'libc.so' on Android

function hookCmp(name) {
  const p = libc.findExportByName(name);
  if (!p) return;
  Interceptor.attach(p, {
    onEnter(args) {
      this.a = args[0].readUtf8String();
      this.b = args[1].readUtf8String();
    },
    onLeave(retval) {
      console.log(`${name}("${this.a}", "${this.b}") = ${retval.toInt32()}`);
    },
  });
  console.log(`[+] ${name}`);
}
['strcmp', 'strncmp', 'strstr', 'strcasecmp'].forEach(hookCmp);

const openPtr = libc.findExportByName('open');
if (openPtr) {
  Interceptor.attach(openPtr, {
    onEnter(args) { this.path = args[0].readUtf8String(); },
    onLeave(retval) { console.log(`open("${this.path}") = ${retval.toInt32()}`); },
  });
  console.log('[+] open');
}
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js
frida -U -n com.example.app -l recipe.js
```

**Tweak this:**
- Noisy? Filter inside `onLeave`, e.g. only log when
  `this.a && this.a.includes('license')`.
- `findExportByName` returns `null` when a symbol is absent (statically linked or
  inlined) — the guards above skip it silently. If nothing fires, the app may use
  its own comparison routine, not libc's; find it via
  [find-string-refs.md](find-string-refs.md).
- Add `strncpy`/`memcmp` the same way (note `memcmp` args are raw buffers, not
  C strings — dump with [dump-buffer.md](dump-buffer.md)).
- Want the caller for a specific hit? Add a backtrace as in
  [trace-native-call.md](trace-native-call.md).
