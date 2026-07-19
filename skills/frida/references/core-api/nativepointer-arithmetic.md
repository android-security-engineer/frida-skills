---
name: nativepointer-arithmetic
description: Do pointer math in a Frida agent — add, sub, and, or, xor, shl, shr, isNull, compare, equals, toString — to compute struct offsets and addresses (Frida 16/17).
---

# NativePointer arithmetic

**When:** you need to compute an address — a struct field offset, an entry in an
array, a base-plus-RVA, or to strip pointer tag bits. NativePointers are
immutable; every operation returns a **new** NativePointer.

```js
const base = Process.getModuleByName('libc.so.6').base;
const field = base.add(0x20);        // base + 0x20, as a new NativePointer
console.log(field);                  // e.g. 0x7f...20
```

## Operations

| Method | Meaning |
| --- | --- |
| `p.add(x)` / `p.sub(x)` | pointer ± offset (x is a number, Int64/UInt64, or pointer) |
| `p.and(x)` / `p.or(x)` / `p.xor(x)` | bitwise ops (mask, set, toggle bits) |
| `p.shl(n)` / `p.shr(n)` | shift left / right by n bits |
| `p.not()` | bitwise NOT |
| `p.isNull()` | true if the pointer is 0 |
| `p.compare(q)` | -1 / 0 / 1 ordering (for sorting or range checks) |
| `p.equals(q)` | true if same address |
| `p.toString([radix])` | hex string by default (`p.toString(10)` for decimal) |
| `p.toInt32()` / `p.toUInt32()` | interpret low bits as a 32-bit int |

Every arithmetic method yields a fresh NativePointer, so you chain them:
`base.add(0x10).and(ptr('0xfffffffffffffff0'))`.

## Indexing an array of pointers

```js
// Walk an array of 8-byte pointers starting at `arr`.
const arr = Memory.alloc(3 * Process.pointerSize);
for (let i = 0; i < 3; i++) {
  const slotPtr = arr.add(i * Process.pointerSize);   // address of slot i
  const value = slotPtr.readPointer();                // pointer stored there
  console.log(i, value);
}
```

`Process.pointerSize` is 8 on 64-bit, 4 on 32-bit — use it instead of hardcoding.

## Comparing and masking

```js
// Page-align a pointer down to a 4 KiB boundary.
const pageMask = ptr(Process.pageSize - 1).not();     // ~0xfff
const pageStart = someAddr.and(pageMask);

// Range check: is `p` within [start, end)?
function inRange(p, start, end) {
  return p.compare(start) >= 0 && p.compare(end) < 0;
}
```

Use `.equals()` for identity and `.compare()` for ordering — the `===` operator
compares object identity, not addresses, so two NativePointers to the same
address are `!==` but `.equals()` true.

## Pitfalls

- **Don't use `+`, `-`, `===`, `<` on NativePointers.** JS operators coerce them
  to strings/NaN and give wrong results. Use the methods above.
- **Offsets are in bytes.** `add(1)` moves one byte, not one element — multiply
  by the element size (e.g. `Process.pointerSize`).
- **Arithmetic doesn't validate mappings.** Computing an address never crashes,
  but *reading* it can — verify the region before dereferencing
  ([nativepointer-read.md](nativepointer-read.md)).
- Large offsets are fine (64-bit safe), but a plain JS number offset above 2^53
  loses precision — pass a `UInt64` instead ([int64-uint64.md](int64-uint64.md)).
