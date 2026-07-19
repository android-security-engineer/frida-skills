---
name: int64-uint64
description: Handle 64-bit integers in a Frida agent with int64/uint64 and Int64/UInt64 objects to avoid JavaScript number precision loss above 2^53 (Frida 16/17).
---

# Int64 and UInt64 — 64-bit math without precision loss

**When:** you deal with values that don't fit in a JS number's 53-bit safe
integer range — file offsets, 64-bit handles, hashes, `int64`/`uint64` return
values, `readU64()` results. Use Frida's 64-bit objects instead of raw numbers.

```js
const a = uint64('0xffffffffffffffff');   // max u64, exact
const b = a.sub(1);
console.log(b.toString(16));              // "fffffffffffffffe" — no rounding
```

Constructors: `int64(x)` / `new Int64(x)` (signed), `uint64(x)` / `new UInt64(x)`
(unsigned). `x` may be a JS number or a string (`'0x…'` or decimal).

## Where they show up

- **`NativeFunction` returns** declared `'int64'`/`'uint64'` → you get an
  `Int64`/`UInt64` (see [nativefunction.md](nativefunction.md)).
- **Pointer reads** `readU64()`/`readS64()` → `UInt64`/`Int64`
  ([nativepointer-read.md](nativepointer-read.md)).
- **`NativePointer` itself** is 64-bit; its `.toString()` gives the hex address.

## Arithmetic and comparison

Like NativePointers, these are immutable and use **methods**, not JS operators:

| Method | Meaning |
| --- | --- |
| `.add(x)` `.sub(x)` `.mul(x)` `.div(x)` `.mod(x)` | arithmetic |
| `.and(x)` `.or(x)` `.xor(x)` `.shr(n)` `.shl(n)` `.not()` | bitwise |
| `.compare(x)` | -1 / 0 / 1 ordering |
| `.equals(x)` | equality |
| `.toNumber()` | to JS number (lossy above 2^53) |
| `.toString([radix])` | string; `.toString(16)` for hex |

```js
const size = uint64('0x100000000');       // 4 GiB, > 2^32
const half = size.div(2);
console.log(half.toString());              // "2147483648"
if (size.compare(uint64(0)) > 0) console.log('non-zero');
```

## Converting to/from JS numbers

- `int64(123)` / `uint64('456')` to build one.
- `.toNumber()` to get a JS number — **only safe below 2^53**; above that it
  rounds. Prefer `.toString()` when you just need to display or log.
- You can pass an `Int64`/`UInt64` (or a number) directly as an `'int64'`/
  `'uint64'` argument to a `NativeFunction`.

## Pitfalls

- **Never do 64-bit math with `+`/`*`/`>`.** JS numbers silently lose precision
  past 2^53; `0xffffffffffffffff + 1` in plain JS is wrong. Use the methods.
- **Signed vs unsigned matters** for `.compare()` and `.shr()`. Pick `Int64` or
  `UInt64` to match the value's real signedness.
- **`.toNumber()` on a large value lies.** Log with `.toString(16)` when the value
  may exceed 2^53.
- An `Int64` and a `UInt64` are distinct types — don't assume methods mix them
  silently; convert intent explicitly.
