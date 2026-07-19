---
name: nativefunction-return
description: Fixes "retval.toInt32 is not a function" and NaN math — a NativeFunction with an 'int'/'uint' return is a plain JS number, not a NativePointer; only Interceptor retval and 'pointer' returns are pointers.
---

# NativeFunction return values (plain numbers vs pointers)

## Symptom

- `TypeError: <result>.toInt32 is not a function` after calling a `NativeFunction`.
- Arithmetic on a return value gives `NaN` or a wrong number.
- You called `.add()`, `.readUtf8String()`, or `.isNull()` on something that is not
  a pointer.

## Cause

People conflate two different return types:

- An **Interceptor** `onLeave(retval)` argument is **always a NativePointer** — it
  has `.toInt32()`, `.add()`, `.readUtf8String()`, `.replace()`, etc.
- A **`NativeFunction`** maps its return by the declared C type:
  - `'int'` / `'uint'` → a plain **JS number** (use it directly, *no* `.toInt32()`).
  - `'pointer'` → a **NativePointer** (use pointer methods).
  - `'int64'` / `'uint64'` → an **Int64** / **UInt64** object (use `.toNumber()`,
    `.add()`).

So `nf().toInt32()` fails when `nf` returns `'int'`, because a number has no such
method.

## Fix

Declare the correct return type and treat the result accordingly:

```js
const getpidPtr = Process.getModuleByName('libc.so.6').getExportByName('getpid');
const getpid = new NativeFunction(getpidPtr, 'int', []);
const pid = getpid();            // plain number — do NOT call .toInt32()
console.log('pid =', pid, pid + 1);   // ordinary JS math works

// A 'pointer' return IS a NativePointer — pointer methods apply:
const strdupPtr = Process.getModuleByName('libc.so.6').getExportByName('strdup');
const strdup = new NativeFunction(strdupPtr, 'pointer', ['pointer']);
const copy = strdup(Memory.allocUtf8String('hi'));   // NativePointer
console.log(copy.readUtf8String());                  // -> "hi"

// A 64-bit return is an Int64/UInt64 object:
// const nf = new NativeFunction(p, 'int64', []);  const v = nf().toNumber();
```

Contrast with an Interceptor, where `retval` **is** a pointer:

```js
Interceptor.attach(getpidPtr, {
  onLeave(retval) {
    console.log('getpid ret =', retval.toInt32());   // valid: retval is a NativePointer
  }
});
```

## Rule of thumb

`.toInt32()` / `.add()` / `.readUtf8String()` belong to **NativePointers**: the
Interceptor `retval`, `args[i]`, and `'pointer'`-typed `NativeFunction` returns.
An `'int'`/`'uint'` `NativeFunction` return is just a number.
