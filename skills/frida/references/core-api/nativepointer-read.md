---
name: nativepointer-read
description: Read memory through a NativePointer in a Frida agent — readUtf8String, readPointer, readU32, readByteArray, and hexdump — instead of the removed Memory.readX helpers (Frida 16/17).
---

# Reading memory through a NativePointer

**When:** you have an address (an `Interceptor` arg, an export, a
`Memory.alloc`) and need the bytes, string, integer, or pointer it holds. In
Frida 16/17 you read **through the pointer**, not via `Memory.readX(ptr)`.

```js
const open = Process.getModuleByName('libc.so.6').getExportByName('open');
Interceptor.attach(open, {
  onEnter(args) {
    // args[0] is a NativePointer to a C string.
    const path = args[0].readUtf8String();
    console.log('open:', path);
  }
});
```

## The read methods

| You want | Call |
| --- | --- |
| C string (UTF-8) | `ptr.readCString()` / `ptr.readUtf8String([len])` |
| UTF-16 / wide string | `ptr.readUtf16String([len])` |
| ANSI string (Windows) | `ptr.readAnsiString([len])` |
| Raw bytes | `ptr.readByteArray(n)` → ArrayBuffer |
| Unsigned int | `ptr.readU8()`, `readU16()`, `readU32()`, `readU64()` |
| Signed int | `ptr.readS8()`, `readS16()`, `readS32()`, `readS64()` |
| A pointer | `ptr.readPointer()` → NativePointer |
| Float / double | `ptr.readFloat()`, `ptr.readDouble()` |

Notes on types:

- `readU32()`/`readS32()` return a plain JS **number**.
- `readU64()`/`readS64()`/`readPointer()` return a `UInt64`/`Int64`/NativePointer
  respectively — 64-bit ints come back as objects to avoid precision loss (see
  [int64-uint64.md](int64-uint64.md)).
- String reads take an optional byte length; omit it to read up to the first NUL.
  A NULL or unmapped pointer makes them return `null` or throw — guard first.

## Reading structs by offset

Combine `.add()` with a typed read to walk a struct. Say a struct is
`{ int id; char* name; }` on a 64-bit target (4 bytes int + 4 pad + 8 ptr):

```js
function dumpRecord(p) {
  const id = p.readS32();               // offset 0
  const namePtr = p.add(8).readPointer(); // offset 8 (after int + padding)
  return { id, name: namePtr.readUtf8String() };
}
```

See [nativepointer-arithmetic.md](nativepointer-arithmetic.md) for `.add`/offset
math.

## hexdump for quick inspection

```js
const buf = Process.getModuleByName('libc.so.6').base;
console.log(hexdump(buf, { length: 64, header: true, ansi: true }));
```

`hexdump(target, options)` prints an offset/hex/ASCII view. `target` may be a
NativePointer or an ArrayBuffer from `readByteArray`. Options: `length`,
`offset`, `header`, `ansi`.

## Pitfalls

- **Bad pointer = crash.** Reading NULL, freed, or unmapped memory can kill the
  target. Check `ptr.isNull()` and be sure the region is mapped (see
  [process-ranges.md](process-ranges.md)) before dereferencing untrusted values.
- **Length matters for strings.** Without a length, a non-terminated buffer reads
  until it hits a NUL somewhere — possibly far away or in unmapped memory.
- **Don't reach for `Memory.readUtf8String(ptr)`** — that free-function form was
  removed; use the pointer methods above.
