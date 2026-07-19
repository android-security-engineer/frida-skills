---
name: nativefunction
description: Call native C functions from a Frida agent with new NativeFunction, covering type strings, argument marshalling, and return-value mapping to JS types (Frida 16/17).
---

# NativeFunction — call native code from JS

**When:** you want to *invoke* a native function yourself — call the original
after a hook, drive an app API, or exercise a routine directly.

```js
// Call libc's getpid() and print the result.
const p = Process.getModuleByName('libc.so.6').getExportByName('getpid');
const getpid = new NativeFunction(p, 'int', []);
console.log('pid =', getpid());   // 'int' return → plain JS number
```

Signature: `new NativeFunction(address, returnType, argTypes[, abi])`.

## Passing arguments

```js
const libc = Process.getModuleByName('libc.so.6');
const open = new NativeFunction(libc.getExportByName('open'), 'int', ['pointer', 'int']);
const read = new NativeFunction(libc.getExportByName('read'), 'int', ['int', 'pointer', 'ulong']);

const O_RDONLY = 0;
const path = Memory.allocUtf8String('/etc/hostname');   // NativePointer
const fd = open(path, O_RDONLY);                         // number

const buf = Memory.alloc(64);                            // NativePointer
const n = read(fd, buf, 63);                             // number of bytes
if (n > 0) console.log(buf.readUtf8String(n));
```

- `'pointer'` args take a `NativePointer` (from an export, `Memory.alloc`, or
  `ptr(...)`). See [memory-alloc.md](memory-alloc.md).
- `'int'`/`'uint'`/`'long'`/`'size_t'` args take plain JS numbers.
- `'int64'`/`'uint64'` args take an `Int64`/`UInt64` or a number — see
  [int64-uint64.md](int64-uint64.md).

## Return-value mapping (get this right)

| Declared return type | JS value you receive |
| --- | --- |
| `'void'` | `undefined` |
| `'int'`, `'uint'`, `'long'`, `'ulong'`, `'size_t'`, `'bool'` | plain JS **number** (no `.toInt32()`) |
| `'pointer'`, `'char*'` | **NativePointer** |
| `'int64'`, `'uint64'` | `Int64` / `UInt64` object |
| `'float'`, `'double'` | JS number |

So for an `'int'` return you use the number directly — **do not** call
`.toInt32()` on it (that method is for the NativePointers you get from
`Interceptor` `args`/`retval`). For a `'pointer'` return you *do* get a
NativePointer and read through it: `strPtr.readUtf8String()`.

## Common type strings

`'void' 'pointer' 'int' 'uint' 'long' 'ulong' 'size_t' 'int64' 'uint64'
'float' 'double' 'bool' 'char*'`. A 4th argument sets ABI when needed, e.g.
`'stdcall'` / `'win64'` on Windows; omit it on Linux/Android/macOS.

## Pitfalls

- **Wrong signature = crash or garbage.** The `argTypes` array must match the C
  prototype's count and types exactly.
- **Calling can block.** A `NativeFunction` runs synchronously on the current
  thread; a blocking call (e.g. `read` on an empty pipe) stalls the agent.
- **errno is not on the return value.** To read `errno`/`lastError` after the
  call, use a [`SystemFunction`](system-functions-errno.md) instead.
- If you need the *original* after `Interceptor.replace`, build the
  `NativeFunction` over the original pointer **before** replacing — see
  [interceptor-replace.md](interceptor-replace.md).
