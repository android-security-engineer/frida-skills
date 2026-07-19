---
name: swap-argument
description: Frida agent that rewrites a function argument in Interceptor.onEnter before the original runs — replace a path, string, flag, or pointer argument.
---

# Rewrite an argument before the original runs

**When:** you want the function to run with a *different* input — redirect a file
path, change a flag, swap a string. Overwrite `args[i]` in `onEnter`; the original
body then sees your value.

```js
// recipe.js — redirect open("/etc/hosts", ...) to a file you control.
const libc = Process.getModuleByName('libc.so.6');   // 'libc.so' on Android
const openPtr = libc.getExportByName('open');

// Allocate the replacement string ONCE at load, not per-call (keep it alive).
const fakePath = Memory.allocUtf8String('/data/local/tmp/hosts');

Interceptor.attach(openPtr, {
  onEnter(args) {
    const path = args[0].readUtf8String();
    if (path === '/etc/hosts') {
      console.log(`redirect open("${path}") -> /data/local/tmp/hosts`);
      args[0] = fakePath;          // replace the char* argument (a NativePointer)
    }
  },
});
console.log('[+] hooked open() for path redirect');
```

Swap an integer flag instead of a pointer:

```js
// Force the 2nd arg (int flags) to a fixed value. Wrap the number in ptr().
Interceptor.attach(openPtr, {
  onEnter(args) { args[1] = ptr(0); },   // e.g. force O_RDONLY (0)
});
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- Integer args are passed as NativePointers here — wrap replacements with `ptr(n)`.
- Allocate strings/buffers at load time (as above) or stash them on `this` so the
  GC doesn't free them mid-call.
- Only change the *return*, not the input? See
  [replace-return-value.md](replace-return-value.md).
- Need to inspect the buffer an arg points at first? See
  [dump-buffer.md](dump-buffer.md).
- For a Java method, set `.implementation` and call the original with new args:
  `this.method(newArg)` inside the override — see
  [android-find-class.md](android-find-class.md).
