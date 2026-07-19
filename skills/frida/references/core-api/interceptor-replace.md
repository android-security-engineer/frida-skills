---
name: interceptor-replace
description: Swap a native function's implementation wholesale with Interceptor.replace and a NativeCallback in a Frida agent, optionally calling the original (Frida 16/17).
---

# Interceptor.replace — swap the implementation

**When:** you need to *fully control* what a function returns or does — skip the
original body, force a value, or wrap it with pre/post logic. Use this instead of
[interceptor-attach.md](interceptor-attach.md) when observing isn't enough.

```js
// Force getuid() to always report root (0).
const getuid = Process.getModuleByName('libc.so.6').getExportByName('getuid');
Interceptor.replace(getuid, new NativeCallback(function () {
  return 0;                       // 'int' return → plain JS number
}, 'int', []));
```

The replacement is a [`NativeCallback`](nativecallback.md): a JS function plus a
return type and an argument-type array that describe the C signature exactly.

## Calling the original from the replacement

Capture a [`NativeFunction`](nativefunction.md) over the *original* pointer
*before* replacing, then call it inside your callback:

```js
const openPtr = Process.getModuleByName('libc.so.6').getExportByName('open');
const openOrig = new NativeFunction(openPtr, 'int', ['pointer', 'int', 'int']);

Interceptor.replace(openPtr, new NativeCallback(function (pathPtr, flags, mode) {
  const path = pathPtr.readUtf8String();
  if (path === '/etc/shadow') {
    return -1;                    // deny this path outright
  }
  return openOrig(pathPtr, flags, mode);   // 'int' → number, return as-is
}, 'int', ['pointer', 'int', 'int']));
```

## Key details

- **Callback params are typed values, not raw NativePointers**, following the
  argument-type array: `'pointer'` args arrive as NativePointers, `'int'` as JS
  numbers. This differs from `Interceptor.attach`, where every `args[i]` is a
  NativePointer.
- **The return value must match the declared return type.** `'int'`/`'uint'` →
  return a JS number; `'pointer'` → return a NativePointer; `'int64'`/`'uint64'`
  → return an `Int64`/`UInt64` (see [int64-uint64.md](int64-uint64.md)).
- **Keep the NativeCallback referenced.** If it is garbage-collected while the
  hook is live, calls into it crash. Assign it to a module-scope variable (a
  top-level `const` as above is fine) — don't create it inline in a short-lived
  scope you then discard.
- Undo with `Interceptor.revert(target)` — see
  [interceptor-revert-flush.md](interceptor-revert-flush.md).

## attach vs replace

| Need | Use |
| --- | --- |
| Log/inspect args and result | `Interceptor.attach` |
| Tweak an arg or the retval, still run original | `Interceptor.attach` (assign `args[i]`, `retval.replace`) |
| Skip the original, decide the return yourself | `Interceptor.replace` |
| Conditionally call original | `Interceptor.replace` + captured `NativeFunction` |

## Pitfalls

- **Signature mismatch corrupts the stack.** The type array must match the real
  C prototype (count and types). Wrong types cause garbage args or crashes.
- **Resolve and wrap the original before replacing.** After `replace`, the
  pointer routes to your callback; a `NativeFunction` captured earlier still
  reaches the original trampoline.
- Replacing very hot functions (allocator, string ops) is risky — a bug takes
  down the whole process. Prefer `attach` unless you truly must intervene.
