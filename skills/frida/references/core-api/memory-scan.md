---
name: memory-scan
description: Search a memory range for a byte pattern in a Frida agent using Memory.scan (async) or Memory.scanSync, with match/complete callbacks and masked patterns (Frida 16/17).
---

# Memory.scan — find a byte pattern in memory

**When:** you need to locate a signature, magic value, or instruction sequence in
a module or heap range — e.g. finding a function to hook when there's no export,
or locating a config blob.

```js
// Scan a module's memory for the ASCII bytes of "root".
const m = Process.getModuleByName('libc.so.6');
Memory.scan(m.base, m.size, '72 6f 6f 74', {   // "root"
  onMatch(address, size) {
    console.log('found at', address);
    // return 'stop';  // optional: end the scan early
  },
  onComplete() {
    console.log('scan finished');
  }
});
```

## The pattern string

- Space-separated hex bytes: `'de ad be ef'`.
- **Wildcards** with `??` for "any byte": `'8b ?? ?? 00 00'`.
- Masked form `bytes:mask` is also accepted, e.g. `'b8ffffff:ff000000'`.

To scan for a string's bytes, either write the hex or build a pattern from a
buffer you control.

## Async vs sync

```js
// Synchronous: returns an array immediately, blocks until done.
const matches = Memory.scanSync(m.base, m.size, '72 6f 6f 74');
matches.forEach(({ address, size }) => console.log(address, size));
```

- `Memory.scan(base, size, pattern, { onMatch, onComplete, onError })` — **async**,
  streams matches via callbacks; won't block other agent work. `onMatch` may
  return `'stop'` to halt.
- `Memory.scanSync(base, size, pattern)` — **blocking**, returns
  `[{ address, size }, …]`. Simpler when you just want all hits and don't mind
  waiting.

`address` in both is a `NativePointer` you can then read
([nativepointer-read.md](nativepointer-read.md)) or hook.

## Choosing the range

Scan a bounded region, not all of memory:

- A module: `m.base` … `m.size` (as above).
- Writable/heap ranges: enumerate with
  [`process-ranges.md`](process-ranges.md) and scan each `range.base`/`range.size`.

```js
Process.enumerateRanges('r--').forEach(range => {
  Memory.scanSync(range.base, range.size, 'ca fe ba be')
    .forEach(m => console.log('hit', m.address));
});
```

## Pitfalls

- **Scanning huge or unmapped ranges is slow or crashes.** Bound the scan to a
  known module or an enumerated range with valid protection.
- **Skipping guard/unmapped pages:** `Memory.scan` handles unreadable pages
  gracefully via `onError`, but passing a wildly wrong base/size can still fault.
  Prefer ranges from enumeration.
- **A too-generic pattern floods matches.** Make the signature long/specific
  enough to be unique.
- Matched addresses may shift between runs (ASLR) — scan at runtime, don't
  hardcode offsets from a previous session.
