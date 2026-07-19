---
name: process-ranges
description: Enumerate memory ranges and malloc ranges in a Frida target — filter by protection to find writable/executable regions, heaps, and the region owning an address.
---

# Process ranges: mapped memory regions

**When:** you need to find writable or executable regions, locate heap/allocated
blocks, bound a [memory-scan.md](memory-scan.md) to a real mapping, or learn the
protection of the region an address lives in.

## Shortest working example

```js
Process.enumerateRanges('r-x').forEach(r =>
  console.log(r.base, '+', r.size, r.protection, r.file && r.file.path));
```

## enumerateRanges

```js
// Filter by minimum protection with a protection string:
Process.enumerateRanges('rw-');        // all readable+writable regions
Process.enumerateRanges('r-x');        // executable code regions
// Or pass an object to also coalesce adjacent ranges:
Process.enumerateRanges({ protection: 'r--', coalesce: true });
```

Each range: `{ base, size, protection, file? }`. `protection` is a string like
`'rw-'`; `file` (when backed by a file) has `{ path, offset, size }`.

```js
const r = Process.findRangeByAddress(ptr('0x...'));
if (r) console.log('lives in', r.protection, 'region at', r.base);
```

`Process.getRangeByAddress(addr)` is the throwing variant.

## Malloc ranges (heap blocks)

```js
Process.enumerateMallocRanges().forEach(r =>
  console.log('heap block', r.base, r.size));
```

`enumerateMallocRanges()` reports individual allocator blocks (where a malloc
introspection backend is available — glibc, macOS, etc.). Useful to scan only live
heap allocations rather than whole `rw-` mappings.

## Scanning within a range

```js
const r = Process.enumerateRanges('rw-')[0];
Memory.scan(r.base, r.size, '48 8b ?? ?? ?? ?? ??', {
  onMatch(addr, size) { console.log('hit', addr); },
  onComplete() {}
});
```

Bounding a scan to a specific range is far faster and safer than guessing sizes;
see [memory-scan.md](memory-scan.md).

## Pitfalls

- The protection string filters by **minimum**: `'r--'` includes `'rw-'` and
  `'rwx'` regions too. Match exactly by comparing `r.protection` yourself.
- Ranges are a snapshot; regions map/unmap as the app runs. Re-enumerate rather
  than caching for long-lived logic.
- `enumerateMallocRanges()` returns nothing on platforms without a malloc
  introspection backend — don't rely on it universally; fall back to `rw-` ranges.
- Reading from an executable-only or guard region can fault; check `r.protection`
  before dereferencing, and consider a `Process.setExceptionHandler` (see
  [process.md](process.md)).
