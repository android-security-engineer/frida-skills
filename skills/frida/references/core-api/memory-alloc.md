---
name: memory-alloc
description: Allocate scratch buffers and strings in a target process from a Frida agent with Memory.alloc, allocUtf8String, copy, and dup for passing to native functions (Frida 16/17).
---

# Memory.alloc — scratch buffers for native calls

**When:** a native function needs a pointer to memory you provide — an output
buffer, an input struct, or a string argument. `Memory.alloc` gives you writable,
process-owned memory and returns a `NativePointer`.

```js
// Give read() a 64-byte output buffer.
const libc = Process.getModuleByName('libc.so.6');
const read = new NativeFunction(libc.getExportByName('read'), 'int', ['int', 'pointer', 'ulong']);

const buf = Memory.alloc(64);          // NativePointer to 64 zeroed bytes
const n = read(0, buf, 63);            // read up to 63 bytes from stdin
if (n > 0) console.log(buf.readUtf8String(n));
```

## Allocating strings

```js
const path = Memory.allocUtf8String('/etc/hostname');   // NUL-terminated UTF-8
const wpath = Memory.allocUtf16String('C:\\file.txt');  // UTF-16 (Windows APIs)
const apath = Memory.allocAnsiString('legacy');         // ANSI (Windows)
```

Each returns a `NativePointer` to freshly allocated, NUL-terminated bytes — pass
it straight to a `'pointer'` or `'char*'` argument (see
[nativefunction.md](nativefunction.md)).

## Copying and duplicating

```js
const src = Memory.allocUtf8String('data');
const dst = Memory.alloc(16);
Memory.copy(dst, src, 5);              // copy 5 bytes src → dst (like memcpy)

const clone = Memory.dup(src, 5);      // alloc 5 bytes + copy; returns pointer
```

- `Memory.copy(dst, src, n)` — copy `n` bytes between existing regions.
- `Memory.dup(ptr, n)` — allocate `n` bytes, copy from `ptr`, return the new
  pointer. Handy to snapshot a buffer before the app mutates it.

## Lifetime and alignment

- Allocated memory is **owned by your script** and lives as long as the
  `NativePointer` (or something derived from it) is reachable in JS. When all
  references are gone, Frida may free it.
- **Keep a reference for as long as native code holds the pointer.** If you pass a
  buffer to native code that stores it for later, keep the JS pointer alive (e.g.
  in a module-scope array) so it isn't freed underneath the target.
- `Memory.alloc(size)` returns page-aligned-ish, zero-initialized memory suitable
  for structs. For a specific alignment, allocate extra and align with
  [`.and()`](nativepointer-arithmetic.md).

## Pitfalls

- **Don't return a buffer and drop its reference** while native code still uses
  it — that's a use-after-free crash. Retain it.
- **Writes must stay within the allocated size.** Writing past the end corrupts
  adjacent allocations — allocate enough, and cap string writes to capacity
  ([nativepointer-write.md](nativepointer-write.md)).
- Allocated memory defaults to read/write, not executable. To place and run code,
  use `Memory.protect`/`Memory.patchCode`
  ([memory-protect-patchcode.md](memory-protect-patchcode.md)).
