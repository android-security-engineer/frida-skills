---
name: debugsymbol
description: Symbolicate addresses in a Frida target with DebugSymbol.fromAddress/fromName — turn pointers into name+module+file:line and resolve names back to addresses.
---

# DebugSymbol: address ↔ name

**When:** you have a raw address (a backtrace frame, a scan hit, a callback return
address) and want a human-readable `name`, owning module, and — if debug info
exists — `file:line`; or you have a symbol name and want its address.

## Shortest working example

```js
const sym = DebugSymbol.fromAddress(ptr('0x...'));
console.log(sym.toString());              // e.g. "0x7f.. libssl.so!SSL_read"
console.log(sym.moduleName, sym.name, sym.fileName, sym.lineNumber);
```

## API

```js
DebugSymbol.fromAddress(addr);            // → DebugSymbol
DebugSymbol.fromName('SSL_read');         // → DebugSymbol (best-effort)
DebugSymbol.getFunctionByName('open');    // → NativePointer (throws if unknown)
DebugSymbol.findFunctionsNamed('malloc'); // → array of NativePointer
DebugSymbol.findFunctionsMatching('SSL_*'); // → array of NativePointer
```

A `DebugSymbol` has: `.address`, `.name`, `.moduleName`, `.fileName`,
`.lineNumber`, and a `.toString()` that formats them compactly.

## Typical use: readable backtraces

```js
Thread.backtrace(this.context, Backtracer.ACCURATE)
  .map(DebugSymbol.fromAddress)
  .forEach(s => console.log(s.toString()));
```

Pairs directly with [thread-backtrace.md](thread-backtrace.md).

## Pitfalls

- Symbolication quality depends on what the target ships. Stripped release
  binaries give you `moduleName + offset` but a `null` `name`/`fileName`; that is
  still enough to correlate with a static disassembler.
- `fileName`/`lineNumber` need DWARF/debug info present in the module — usually
  absent in production apps.
- `fromAddress` is not free (it searches symbol tables). Don't call it per-event in
  a hot hook; collect addresses and resolve lazily, or cache results in a JS `Map`.
- `getFunctionByName` **throws** when the name is unknown — wrap in try/catch or use
  `findFunctionsNamed` (empty array on miss). For plain export lookup prefer a
  Module instance from [module.md](module.md); `DebugSymbol` shines for
  local/debug symbols and reverse (address→name) mapping.
