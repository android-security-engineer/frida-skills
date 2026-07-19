---
name: stale-removed-api
description: Fixes "TypeError: Module.getExportByName is not a function" and similar — Frida 17 removed the static Module.getExportByName/findExportByName and Memory.read* free functions; use the pointer/instance forms.
---

# Stale / removed API (Frida 17)

## Symptom

Your agent throws on a call that "used to work" (and appears in old tutorials):

- `TypeError: Module.getExportByName is not a function`
- `TypeError: Module.findExportByName is not a function`
- `TypeError: Memory.readUtf8String is not a function`

## Cause

Frida 17 **removed the static module helpers** `Module.getExportByName()` and
`Module.findExportByName()`, and the old free-function memory readers
(`Memory.readUtf8String(ptr)`, `Memory.writeX(ptr, ...)`). Training data and blog
posts written for Frida ≤15 still show them. They are gone.

## Fix — exports

Resolve exports through a **Module instance** or the global lookup:

```js
// Old (removed):  Module.getExportByName('libc.so.6', 'open')
// New — instance method (throws if the module is absent):
const openPtr = Process.getModuleByName('libc.so.6').getExportByName('open');

// New — null-returning variants:
const mod = Process.findModuleByName('libc.so.6');   // null if not loaded
const p = mod && mod.findExportByName('open');        // null if no such export

// New — search every loaded module at once:
const malloc = Module.getGlobalExportByName('malloc');

console.log('open @', openPtr, 'malloc @', malloc);
```

## Fix — reading/writing memory

Call the read/write methods **on the NativePointer**, not on `Memory`:

```js
const p = Process.getModuleByName('libc.so.6').getExportByName('getenv');
// Old (removed):  Memory.readUtf8String(somePtr)
// New — through the pointer:
Interceptor.attach(p, {
  onEnter(args) {
    const name = args[0].readUtf8String();     // read THROUGH the pointer
    console.log('getenv:', name);
    // writing works the same way: args[0].writeUtf8String('PATH');
  }
});
```

`Memory` still owns *allocation* and bulk ops (`Memory.alloc`,
`Memory.allocUtf8String`, `Memory.protect`, `Memory.scan`, `hexdump`) — just not
the per-value `read*`/`write*` accessors.

## Verify

Run the agent; the `TypeError` is gone and pointers print as `0x…` addresses. If a
resolved export is `null`, the module may not be loaded yet — see
[hooks-never-fire.md](hooks-never-fire.md).
