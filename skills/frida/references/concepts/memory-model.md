---
name: memory-model
description: Explains the target's memory model — address space, modules, ranges, protections, and NativePointers as process-local handles — so an agent can read, write, and scan safely.
---

# Memory model: address space, modules, and pointers

The agent runs inside the target and sees its **virtual address space** directly.
Understanding how that space is organized — and that a pointer is only meaningful
in that process — is the basis for safe reading, writing, and scanning.

## The address space is made of modules and ranges

A running process is a set of mapped regions:

- **Modules** — loaded executables and shared libraries (`libc.so.6`, the app
  binary, `.dll`s). Each has a base address, size, path, and export/symbol tables.
- **Ranges** — contiguous regions with memory **protections** (`r--`, `rw-`,
  `r-x`, …). Code is typically `r-x`, data `rw-`, constants `r--`.

Enumerate them from the agent:

```js
Process.enumerateModules().slice(0, 3).forEach(m =>
  console.log(m.name, m.base, m.size));

const libc = Process.getModuleByName('libc.so.6');   // throws if absent
const open = libc.getExportByName('open');           // NativePointer to the symbol
console.log('open @', open);

Process.enumerateRanges('r-x').slice(0, 3).forEach(r =>
  console.log(r.base, r.size, r.protection));
```

Note the Frida 17 form: resolve exports **through a Module instance**
(`libc.getExportByName('open')`) or globally with
`Module.getGlobalExportByName('open')` — the old static
`Module.getExportByName(...)` was removed.

## Pointers are process-local handles

A `NativePointer` is a raw address **inside the target**. It is meaningful only in
that process — you cannot send it to the host and dereference it there
([host-vs-agent.md](host-vs-agent.md)). Create and manipulate them in the agent:

```js
const p = ptr('0x7fff00001000');
console.log(p.add(0x10), p.isNull(), p.compare(NULL));
```

## Read and write THROUGH the pointer

Access memory via the pointer's own methods — **not** removed free functions like
`Memory.readUtf8String(ptr)`:

```js
const s   = p.readUtf8String();      // read a C string at p
const n   = p.readU32();             // read a 32-bit value
const buf = p.readByteArray(64);     // raw bytes → ArrayBuffer
p.writeInt(0);                        // write (target must be writable!)
console.log(hexdump(p, { length: 64 }));
```

Writing to `r--`/`r-x` memory faults. Make it writable first, or patch code
through the proper helper:

```js
Memory.protect(p, 16, 'rwx');        // change protection on a range
Memory.patchCode(codePtr, 16, code => {  // safe self-modifying-code path
  // use an arch-specific writer here, e.g. new Arm64Writer(code) / new X86Writer(code)
});
```

## Allocating and scanning

- **Allocate** scratch memory owned by the agent:
  `Memory.alloc(64)`, `Memory.allocUtf8String('hi')`. It stays valid while a JS
  reference exists.
- **Scan** for a byte pattern within a range:

```js
const m = Process.getModuleByName('libc.so.6');
Memory.scan(m.base, m.size, '00 ff ?? 11', {
  onMatch(address, size) { console.log('hit', address); },
  onComplete() { console.log('done'); }
});
// synchronous variant: Memory.scanSync(m.base, m.size, '00 ff ?? 11')
```

## Safety rules that prevent crashes

- **A bad write crashes the target** — the agent has full, unchecked access. Verify
  the address and its protection before writing.
- **Respect pointer size / arch** — use `Process.pointerSize` and arch-specific
  writers; don't assume 64-bit.
- **Don't hold stale pointers** — memory can be unmapped (e.g. a library unloads);
  re-resolve from modules rather than caching raw addresses across time.
- **Keep allocations alive** — lose the JS reference and `Memory.alloc` memory may
  be reclaimed.

For hooking functions at these addresses, see the core-api Interceptor docs; for
why the agent can touch all of this directly, see
[architecture.md](architecture.md).
