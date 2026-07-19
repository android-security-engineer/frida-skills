---
name: interceptor-attach
description: Hook a native function with Interceptor.attach to observe or tweak arguments and return value via onEnter/onLeave in a Frida agent (Frida 16/17).
---

# Interceptor.attach — observe and adjust calls

**When:** you want to see (or lightly modify) a function's arguments and return
value *without* replacing its body. This is the default hooking tool.

这张图回答："一次被 hook 的调用经过哪两步回调？"

```mermaid
flowchart LR
  C["caller"] --> T["trampoline"]
  T --> E["onEnter(args)"]
  E --> O["original"]
  O --> L["onLeave(retval)"]
  L --> R["return to caller"]
```

```js
// Log every open() call in libc and its result.
const open = Process.getModuleByName('libc.so.6').getExportByName('open');
Interceptor.attach(open, {
  onEnter(args) {
    // args[0] is a NativePointer to the path string.
    this.path = args[0].readUtf8String();
  },
  onLeave(retval) {
    // retval is a NativePointer; the fd is its 32-bit int value.
    console.log(`open("${this.path}") = ${retval.toInt32()}`);
  }
});
```

## Key details

- **`target`** is a `NativePointer` to the function (from an export, symbol, or
  address). See [nativefunction.md](nativefunction.md) for resolving addresses.
- **`args[i]` are NativePointers**, always — even for integers. A C `int` is in
  the pointer's low bits: `args[0].toInt32()`. A C `char*` is the pointer
  itself: `args[0].readUtf8String()`. See [nativepointer-read.md](nativepointer-read.md).
- **`retval` is a NativePointer.** Get an int with `retval.toInt32()`; replace it
  with `retval.replace(ptr(0))` or `retval.replace(newNativePointer)`.
- **`this` persists** from `onEnter` to `onLeave` for the same call — stash data
  on it (`this.path` above). It also exposes:
  - `this.returnAddress` — caller address (NativePointer).
  - `this.context` — CPU registers (`this.context.pc`, `.sp`, `.x0`…). Usable
    with [thread-backtrace.md](thread-backtrace.md).
  - `this.threadId`, `this.errno` (POSIX) / `this.lastError` (Windows).
- **Either callback is optional.** Omit `onLeave` if you only inspect inputs.
- You may return early logic in `onEnter`, but you cannot skip the original call
  from here — for that, replace it: [interceptor-replace.md](interceptor-replace.md).

## Modifying arguments

Overwrite an argument slot before the call proceeds:

```js
const read = Process.getModuleByName('libc.so.6').getExportByName('read');
Interceptor.attach(read, {
  onEnter(args) {
    // Clamp the requested count (3rd arg, size_t) to 16 bytes.
    if (args[2].toInt32() > 16) args[2] = ptr(16);
  }
});
```

Assigning `args[i] = ptr(...)` replaces that argument. To point at your own
buffer, allocate one first — see [memory-alloc.md](memory-alloc.md).

## Pitfalls

- **Hot functions cost CPU.** Attaching to something like `malloc` or `memcpy`
  and logging each call can slow or hang the target. Filter early and keep
  callbacks minimal.
- **Reading a bad pointer crashes the target.** A `char*` arg may be NULL; guard
  with `if (!args[0].isNull())` before `readUtf8String()`.
- **Return type matters.** `retval.toInt32()` for `int`, but for a pointer
  return keep it as the NativePointer. A 64-bit return needs
  `retval.toString()` or reinterpretation — see [int64-uint64.md](int64-uint64.md).
- **onLeave never fires if the function doesn't return** (e.g. `exit`, `pthread`
  workers that loop forever, or a `longjmp`). Don't rely on paired cleanup there.
- Inlined or stripped functions may have no stable address to attach to; resolve
  via [apiresolver.md](apiresolver.md) or symbols first.
