---
name: nativepointer-write
description: Write memory through a NativePointer in a Frida agent — writeUtf8String, writePointer, writeU32, writeByteArray — plus the protection pitfalls of patching read-only pages (Frida 16/17).
---

# Writing memory through a NativePointer

**When:** you need to change a value in the target — patch a flag, overwrite a
string an app is about to use, or fill a scratch buffer. As with reads, you write
**through the pointer**, not via `Memory.writeX(ptr, …)`.

```js
// Allocate a buffer and write a string into it.
const buf = Memory.alloc(64);
buf.writeUtf8String('hello');
console.log(buf.readUtf8String());   // "hello"
```

## The write methods

| You want to write | Call |
| --- | --- |
| C string (UTF-8) | `ptr.writeUtf8String('text')` |
| UTF-16 / ANSI string | `ptr.writeUtf16String(...)` / `ptr.writeAnsiString(...)` |
| Raw bytes | `ptr.writeByteArray([0x90, 0x90])` or an ArrayBuffer |
| Unsigned int | `ptr.writeU8(v)`, `writeU16`, `writeU32`, `writeU64` |
| Signed int | `ptr.writeS8(v)`, `writeS16`, `writeS32`, `writeS64` |
| A pointer | `ptr.writePointer(otherPtr)` |
| Float / double | `ptr.writeFloat(v)`, `ptr.writeDouble(v)` |

- Write calls **return the pointer**, so they chain:
  `buf.writeU32(1).add(4).writeU32(2);`.
- 64-bit writes accept an `Int64`/`UInt64` or a JS number:
  `ptr.writeU64(uint64('0xdeadbeef'))` — see [int64-uint64.md](int64-uint64.md).
- `writeByteArray` takes a plain JS array of byte values or an ArrayBuffer.

## Modifying a value inside a hook

```js
// Force the 3rd arg's target flag to 0 before the call runs.
const flagPtr = /* a NativePointer into the target's data */ Memory.alloc(4);
flagPtr.writeU32(1);
Interceptor.attach(Process.getModuleByName('libc.so.6').getExportByName('puts'), {
  onEnter(args) {
    // Overwrite the string puts() is about to print (writable heap only!).
    // args[0].writeUtf8String('patched');   // see pitfall below
  }
});
```

## Writable vs read-only memory

- **Heap, stack, and `Memory.alloc` buffers are writable** — write freely.
- **Code and many string literals live in read-only pages.** Writing there throws
  an access violation. To patch code or `.rodata`, first make the page writable:
  `Memory.protect(ptr, size, 'rwx')`, or use `Memory.patchCode()` which handles
  protection and cache flushing for you. See
  [memory-protect-patchcode.md](memory-protect-patchcode.md).
- **Overwriting a longer string in place overflows** into neighboring bytes. Only
  write a string as long as the original buffer, or allocate a new buffer with
  `Memory.allocUtf8String` and repoint the argument
  ([memory-alloc.md](memory-alloc.md)).

## Pitfalls

- **Writing to read-only pages crashes** unless you `Memory.protect` first.
- **String overrun corrupts adjacent data** — respect the original capacity.
- **Endianness/size must match** the field: use `writeU32` for a 32-bit field,
  not `writeU64`, or you clobber the next field.
- **Don't use `Memory.writeUtf8String(ptr, s)`** — removed; use the pointer
  method.
