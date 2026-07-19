---
name: trace-native-call
description: Frida agent that logs a native/libc function's arguments, return value, and backtrace on every call — trace open, connect, or any export.
---

# Trace a native call (args + return + backtrace)

**When:** you want to see every call to a native export — its arguments, what it
returned, and who called it. This is the workhorse recon hook.

```js
// recipe.js — trace open(2): path + flags in, fd out, plus caller backtrace
const libc = Process.getModuleByName('libc.so.6');   // 'libc.so' on Android, 'libSystem.B.dylib' on iOS/macOS
const openPtr = libc.getExportByName('open');

Interceptor.attach(openPtr, {
  onEnter(args) {
    // args[i] are NativePointers. arg0 = char* path, arg1 = int flags.
    this.path = args[0].readUtf8String();
    this.flags = args[1].toInt32();
  },
  onLeave(retval) {
    // retval is a NativePointer; this is an int-typed return, so .toInt32().
    const fd = retval.toInt32();
    console.log(`open("${this.path}", 0x${this.flags.toString(16)}) = ${fd}`);
    if (fd < 0) {
      console.log('  backtrace:\n  ' +
        Thread.backtrace(this.context, Backtracer.ACCURATE)
          .map(DebugSymbol.fromAddress).join('\n  '));
    }
  },
});
console.log('[+] hooked open()');
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn (Android/iOS)
frida -n myprocess -l recipe.js               # attach by name (local)
```

**Tweak this:**
- Different function: change `'open'` and the arg parsing. Strings →
  `args[i].readUtf8String()`, ints → `args[i].toInt32()`, raw pointers → leave as-is.
- Only backtrace on interesting calls (as above) — full backtraces on a hot
  function flood the log. See [count-and-time-calls.md](count-and-time-calls.md).
- Symbol not found via one module? Try `Module.getGlobalExportByName('open')`.
- Reading a buffer arg instead of a string? See [dump-buffer.md](dump-buffer.md).
