---
name: module-map
description: Use Frida's ModuleMap to map an arbitrary address back to its owning module quickly, and to test whether an address belongs to a set of modules.
---

# ModuleMap: address → owning module, fast

**When:** you have many addresses (backtrace frames, scan hits, callback return
addresses) and need to know which module each belongs to. A `ModuleMap` snapshots
the module layout once, then answers lookups without re-enumerating.

## Shortest working example

```js
const map = new ModuleMap();
const ret = ptr('0x7f... some address ...');
console.log(map.findName(ret));   // 'libssl.so' or null
console.log(map.find(ret));       // the Module, or null
```

## Why not just call Process.getModuleByAddress each time

`Process.getModuleByAddress(addr)` walks the live module list on every call. When
you resolve hundreds of frames (e.g. filtering a
[thread-backtrace.md](thread-backtrace.md)), a cached `ModuleMap` is far cheaper.

## API

```js
const map = new ModuleMap();          // snapshot of all modules now
map.has(addr);                        // boolean: inside any mapped module?
map.find(addr);                       // Module or null
map.findName(addr);                   // String name or null
map.findPath(addr);                   // String path or null
map.values();                         // array of Modules in the map
map.update();                         // re-snapshot after libraries (un)load
```

### Filtering to a subset of modules

Pass a predicate to include only modules you care about — useful to keep just the
app's own libraries and treat everything else as "system":

```js
const appMap = new ModuleMap(m => m.path.includes('/app/'));
Thread.backtrace(this.context, Backtracer.ACCURATE)
  .filter(addr => appMap.has(addr))      // keep only app frames
  .forEach(addr => console.log(DebugSymbol.fromAddress(addr)));
```

## Pitfalls

- A `ModuleMap` is a **snapshot**. If the target loads or unloads libraries after
  you build it, call `map.update()` or the lookups go stale (missing new modules,
  or pointing at an unmapped range).
- `find`/`findName` return `null` for addresses outside every mapped module (heap,
  stack, JIT). That's expected — test with `has()` first if you branch on it.
- The predicate form only *filters* the snapshot; it does not keep watching for new
  modules. Re-create or `update()` after `dlopen`.
- For one-off single lookups, `Process.getModuleByAddress()` /
  `Process.findModuleByAddress()` are simpler — reach for `ModuleMap` when the
  lookup is hot. See [module.md](module.md) and [process.md](process.md).
