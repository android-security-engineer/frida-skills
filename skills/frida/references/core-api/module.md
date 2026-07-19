---
name: module
description: Work with loaded modules in Frida 17 — resolve exports/imports/symbols, read base/size/path, and load libraries, without the removed static Module helpers.
---

# Module: libraries loaded in the target

**When:** you need the address of a function, the load base of a library, or a
list of what a `.so`/`.dylib`/`.dll` exports — before hooking with
[interceptor-attach.md](interceptor-attach.md) or calling it via
[nativefunction.md](nativefunction.md).

## Shortest working example

```js
const m = Process.getModuleByName('libc.so.6');   // throws if not loaded
console.log(m.name, m.base, m.size, m.path);
const open = m.getExportByName('open');           // NativePointer
console.log('open @', open);
```

## Getting a Module

```js
Process.getModuleByName('libssl.so');   // Module, throws if absent
Process.findModuleByName('libssl.so');  // Module or null
Process.getModuleByAddress(ptr('0x...'));// owning module of an address
Process.enumerateModules();             // array of every loaded Module
Module.load('/data/local/tmp/mylib.so');// force-load, returns the Module
```

Frida 17 **removed** the static `Module.getExportByName()` and
`Module.findExportByName()`. Resolve exports through a Module instance, or search
every module at once with `Module.getGlobalExportByName('malloc')`.

## Fields & methods on a Module instance

| Member | Meaning |
| --- | --- |
| `.name` `.path` | file name and full on-disk path |
| `.base` `.size` | load address (NativePointer) and mapped size (Number) |
| `.getExportByName(n)` | export address, **throws** if missing |
| `.findExportByName(n)` | export address, `null` if missing |
| `.enumerateExports()` | `[{type,name,address}]` — `type` is `'function'`/`'variable'` |
| `.enumerateImports()` | `[{type,name,module,address}]` |
| `.enumerateSymbols()` | `[{isGlobal,type,name,address,...}]` (needs symbol tables) |

```js
const m = Process.getModuleByName('libssl.so');
m.enumerateExports()
  .filter(e => e.name.startsWith('SSL_'))
  .slice(0, 5)
  .forEach(e => console.log(e.name, e.address));
```

## Global export lookup

```js
const malloc = Module.getGlobalExportByName('malloc'); // throws if unresolved
const free   = Module.findGlobalExportByName('free');   // null if unresolved
```

Use this when you don't care which library provides the symbol. It is slower than
a targeted `Process.getModuleByName(lib).getExportByName(...)`.

## Pitfalls

- A library you want may not be loaded yet at spawn time. Hook the loader (e.g.
  `dlopen`/`android_dlopen_ext`) and resolve **after** it returns, or gate on
  `Process.findModuleByName(...)` returning non-null.
- `enumerateSymbols()` returns local/debug symbols only if the module ships a
  symbol table; stripped release libraries expose exports only.
- `.base` is a NativePointer; `.size` is a plain Number. Do arithmetic with
  `.add()`/`.sub()` on the base — see
  [nativepointer-arithmetic.md](nativepointer-arithmetic.md).
- Names are case-sensitive and platform-specific (`libc.so.6` on Linux,
  `libSystem.B.dylib` on macOS, `kernel32.dll` on Windows).
- To map an address back to a module repeatedly, build a
  [module-map.md](module-map.md) instead of scanning every time.
