---
name: nativecallback
description: Build a native-callable function from JS with new NativeCallback for Interceptor.replace targets or C callbacks in a Frida agent, keeping it alive to avoid crashes (Frida 16/17).
---

# NativeCallback — expose a JS function to native code

**When:** native code needs a function *pointer* implemented in JS — the
replacement body for [`Interceptor.replace`](interceptor-replace.md), or a
callback you hand to a C API (comparator, signal handler, thread entry).

```js
// A replacement that makes access() always succeed (return 0).
const access = Process.getModuleByName('libc.so.6').getExportByName('access');
const cb = new NativeCallback(function (pathPtr, mode) {
  return 0;                       // 'int' return → plain JS number
}, 'int', ['pointer', 'int']);
Interceptor.replace(access, cb);
```

Signature: `new NativeCallback(jsFunction, returnType, argTypes[, abi])`. The
type strings are the same set as [`NativeFunction`](nativefunction.md).

## Arguments arrive as typed values

Inside the callback, each parameter is decoded per `argTypes`:

- `'pointer'`/`'char*'` → a **NativePointer** (read through it:
  `pathPtr.readUtf8String()`).
- `'int'`/`'uint'`/`'long'`/`'size_t'`/`'bool'` → plain JS **number**.
- `'int64'`/`'uint64'` → `Int64`/`UInt64` (see [int64-uint64.md](int64-uint64.md)).

Your **return** must match the declared return type: a JS number for `'int'`, a
NativePointer for `'pointer'`, an `Int64` for `'int64'`, and nothing/`undefined`
for `'void'`.

## Using it as a raw callback pointer

A `NativeCallback` *is* a `NativePointer`, so you can pass it wherever a C
function pointer is expected — e.g. via a [`NativeFunction`](nativefunction.md):

```js
// Register an atexit() handler written in JS.
const atexit = new NativeFunction(
  Process.getModuleByName('libc.so.6').getExportByName('atexit'),
  'int', ['pointer']);

const onExit = new NativeCallback(function () {
  console.log('process is exiting');
}, 'void', []);

atexit(onExit);                   // native code will call back into JS
```

## Keep it alive (the #1 crash)

Frida's garbage collector can free a `NativeCallback` once no JS reference
remains. If native code later calls a freed callback, the process **crashes**.
Hold a reference for the callback's entire useful life:

```js
const kept = [];                  // module-scope, never goes out of scope
kept.push(onExit);                // now safe as long as the script is loaded
```

A top-level `const` (as in the `access` example) is already a durable reference.
The danger is creating a callback inside a function that returns, dropping the
only reference while native code still holds the pointer.

## Pitfalls

- **Signature must match the real prototype.** Wrong arg count/types corrupt the
  stack when native code invokes the callback.
- **Don't throw across the native boundary.** An uncaught JS exception inside a
  callback invoked from native code has no sane place to propagate; catch and
  return a sensible value instead.
- **Return the right type.** Returning a NativePointer where `'int'` is declared
  (or vice versa) yields garbage in the caller.
