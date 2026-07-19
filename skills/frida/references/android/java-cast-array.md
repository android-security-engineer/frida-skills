---
name: java-cast-array
description: Converting Android Java objects with Java.cast, building primitive arrays with Java.array, handling byte[] ([B), boxing, and String/byte[] conversions in Frida.
---

# Java.cast, Java.array, and type conversions

**When to use:** a hook hands you an `Object` (or a base type) but you need the
concrete class's methods/fields, or you must construct a `byte[]`/`int[]` to pass
into a Java call.

## Java.cast — view an object as the right class

```js
Java.perform(() => {
  const ByteString = Java.use('okio.ByteString');
  const Object = Java.use('java.lang.Object');
  // suppose a hook gave you `objArg` typed as java.lang.Object:
  // const bs = Java.cast(objArg, ByteString);
  // console.log(bs.hex());
});
```

`Java.cast(handle, WrapperClass)` re-wraps an existing instance so you can reach
methods/fields the declared type hid. It does **not** copy or convert the object —
it must actually be an instance of that class, or calls will throw.

## Java.array — build primitive arrays

```js
Java.perform(() => {
  const data = Java.array('byte', [0x41, 0x42, 0x43]);   // byte[] {A,B,C}
  const nums = Java.array('int', [1, 2, 3]);

  const String = Java.use('java.lang.String');
  const s = String.$new(data);            // new String(byte[])
  console.log(s.toString());              // "ABC"
});
```

Element type strings: `'byte'`, `'int'`, `'long'`, `'short'`, `'char'`,
`'boolean'`, `'float'`, `'double'`. For object arrays, pass the JVM descriptor as
the type (e.g. build via a hooked method rather than by hand when possible).

## byte[] to/from JS

A Java `byte[]` returned to your hook is array-like (`.length`, indexable). To get
readable bytes, wrap and convert:

```js
Java.perform(() => {
  const Base64 = Java.use('android.util.Base64');
  const bytes = Java.array('byte', [1, 2, 3, 4]);
  const b64 = Base64.encodeToString(bytes, 0);   // flag 0 = DEFAULT
  console.log('[b64] ' + b64);
});
```

To hexdump raw bytes, convert signed Java bytes (`-128..127`) with `& 0xff`.

## Boxing and primitives

Pass primitives as plain JS numbers/booleans. When a method needs a boxed
`Integer`/`Long`, construct it: `Java.use('java.lang.Integer').$new(5)` — see
[java-constructors.md](java-constructors.md).

## Pitfalls

- **`[B` is the descriptor for `byte[]`** in `.overload('[B')`, but the element
  type for `Java.array` is `'byte'`. Don't mix them up.
- **Casting to an unrelated class** throws `ClassCastException` on first use, not
  at the `cast` call. Confirm the real type first via
  [java-enumerate.md](java-enumerate.md).
- **Signed bytes.** Java `byte` is signed; mask with `& 0xff` before treating as
  an unsigned octet.
- **String encoding.** `new String(byte[])` uses the platform charset; specify a
  charset overload for deterministic UTF-8 when it matters.
