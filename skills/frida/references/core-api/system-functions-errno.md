---
name: system-functions-errno
description: Call native functions and read errno/lastError afterward using SystemFunction, or grab errno inside an Interceptor hook via this.errno, in a Frida agent (Frida 16/17).
---

# SystemFunction and errno — capture the failure code

**When:** a native call can fail and you need *why* — the POSIX `errno` (Linux/
macOS/Android) or Windows `lastError` — atomically with the call's return value.
A plain [`NativeFunction`](nativefunction.md) gives you only the return value.

```js
// open() a missing file and read errno in one shot.
const open = new SystemFunction(
  Process.getModuleByName('libc.so.6').getExportByName('open'),
  'int', ['pointer', 'int']);

const path = Memory.allocUtf8String('/no/such/file');
const result = open(path, 0);
console.log('ret =', result.value);    // -1  ('int' → plain number)
console.log('errno =', result.errno);  // 2   (ENOENT)
```

## What SystemFunction returns

Unlike `NativeFunction`, a `SystemFunction` call returns an **object**, not the
bare value:

- `result.value` — the return value, mapped exactly like `NativeFunction`
  (`'int'` → number, `'pointer'` → NativePointer, `'int64'` → Int64…).
- `result.errno` — the POSIX `errno` captured right after the call (Unix-like).
- `result.lastError` — the Windows `GetLastError()` value (on Windows).

The constructor signature is identical to `NativeFunction`:
`new SystemFunction(address, returnType, argTypes[, abi])`.

## errno inside an Interceptor hook

If you're *hooking* a function rather than calling it, read the code on the
interceptor's `this` context instead — no `SystemFunction` needed:

```js
const read = Process.getModuleByName('libc.so.6').getExportByName('read');
Interceptor.attach(read, {
  onLeave(retval) {
    if (retval.toInt32() === -1) {
      // this.errno on POSIX; this.lastError on Windows.
      console.log('read failed, errno =', this.errno);
    }
  }
});
```

`this.errno` / `this.lastError` reflect the value the *target's* call produced,
read in `onLeave` before your other logic clobbers it.

## Key details

- Reach for `SystemFunction` **only** when you care about the error code. For
  calls where you don't, `NativeFunction` is lighter.
- `result.value` follows the same return-type mapping rules — see the table in
  [nativefunction.md](nativefunction.md). For an `'int'` return it's already a
  plain number; don't call `.toInt32()` on it.
- errno is thread-local; `SystemFunction` captures it on the calling thread
  immediately, avoiding races with later calls that would overwrite it.

## Pitfalls

- **Reading `errno` too late.** If you call a `NativeFunction` and then try to
  fetch errno separately, an intervening call may have already reset it — that's
  the whole reason `SystemFunction` exists.
- **Wrong platform field.** Use `.errno` on POSIX, `.lastError` on Windows; the
  irrelevant one is absent.
- Signature-matching rules are the same as `NativeFunction` — a wrong type array
  still crashes.
