---
name: enumerate-modules-exports
description: Frida agent that lists loaded modules and enumerates a module's exports, imports, and symbols to find a hookable function name or address.
---

# Enumerate modules and exports to find a hook point

**When:** you don't yet know *what* to hook. List modules, then dump one module's
exports/symbols to find the function you want.

```js
// recipe.js — list modules, then dump exports of a chosen one.
console.log('[*] modules:');
Process.enumerateModules().forEach(m => {
  console.log(`  ${m.name}  base=${m.base}  size=0x${m.size.toString(16)}  ${m.path}`);
});

// Pick a module and enumerate its exported functions.
const target = Process.getModuleByName('libapp.so');   // change to your module
console.log(`\n[*] exports of ${target.name}:`);
target.enumerateExports().forEach(e => {
  // e = { type: 'function'|'variable', name, address }
  console.log(`  ${e.type.padEnd(8)} ${e.name}  @ ${e.address}`);
});
```

Filter exports/symbols by a keyword, and fall back to symbols when exports are thin:

```js
// recipe-filter.js — grep for anything matching /crypt|key|sign/i.
const mod = Process.getModuleByName('libapp.so');
const rx = /crypt|key|sign|verify/i;

mod.enumerateExports().filter(e => rx.test(e.name))
  .forEach(e => console.log(`export ${e.name} @ ${e.address}`));

// Stripped binary? Symbols (incl. local) sometimes reveal more:
mod.enumerateSymbols().filter(s => rx.test(s.name))
  .forEach(s => console.log(`symbol ${s.name} @ ${s.address}`));
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- `Process.findModuleByName(name)` returns `null` instead of throwing when unsure a
  module is loaded; `getModuleByName` throws.
- Also `.enumerateImports()` to see what a module *calls* (useful to find libc funcs
  it relies on), and `Module.getGlobalExportByName('malloc')` to search all modules.
- Once you have an address, hook it: [trace-native-call.md](trace-native-call.md).
- Prefer a fuzzy resolver over manual filtering? `new ApiResolver('module')` matches
  `exports:*!*crypt*` patterns across modules.
