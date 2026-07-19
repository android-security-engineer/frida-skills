---
name: java-overloads
description: Resolving overloaded Android Java methods with .overload(signature...), fixing the "has more than one overload" error, and hooking all variants.
---

# Resolving overloads with .overload(...)

**When to use:** a Java method name maps to several signatures (very common:
`StringBuilder.append`, `Cipher.doFinal`, `Log.d`). Assigning `.implementation`
directly then throws:

```
Error: c.m(): has more than one overload, use .overload(<signature>) to choose from:
	.overload('int')
	.overload('java.lang.String')
	...
```

## Shortest working example

```js
Java.perform(() => {
  const Str = Java.use('java.lang.String');
  // String(byte[]) constructor is also overloaded; here a method example:
  const SB = Java.use('java.lang.StringBuilder');
  SB.append.overload('java.lang.String').implementation = function (s) {
    console.log('[append] ' + s);
    return this.append(s);
  };
});
```

## Writing the signature

- Pass the **parameter types**, in order, as strings — exactly as the error dump
  prints them. Frida already lists valid overloads in the error; copy one.
- Primitives are lowercase: `'int'`, `'long'`, `'boolean'`, `'byte'`, `'float'`,
  `'double'`, `'char'`, `'short'`. Objects are fully qualified: `'java.lang.String'`.
- **Arrays** use JVM descriptors: `byte[]` → `'[B'`, `int[]` → `'[I'`,
  `String[]` → `'[Ljava.lang.String;'`, `Object[]` → `'[Ljava.lang.Object;'`.
- **No-arg** overload: `.overload()` with no arguments.

```js
Java.perform(() => {
  const Cipher = Java.use('javax.crypto.Cipher');
  Cipher.doFinal.overload('[B').implementation = function (input) {
    const out = this.doFinal(input);
    console.log('[doFinal] in=' + input.length + ' out=' + out.length);
    return out;
  };
});
```

## Hooking every overload at once

Iterate `.overloads` when you don't care which signature fires:

```js
Java.perform(() => {
  const Log = Java.use('android.util.Log');
  Log.d.overloads.forEach((ov) => {
    ov.implementation = function () {
      // arguments is array-like; forward all of them
      console.log('[Log.d] ' + Array.prototype.join.call(arguments, ' | '));
      return ov.apply(this, arguments);
    };
  });
});
```

`ov.apply(this, arguments)` calls that specific original overload with the exact
args received.

## Pitfalls

- **Wrong descriptor for arrays** is the most common mistake. `byte[]` is `'[B'`,
  never `'byte[]'`. Copy from the error dump to be safe.
- **Ambiguous numeric literals.** When calling (not hooking) an overloaded method
  from JS, Frida may pick the wrong numeric overload; select explicitly with
  `.overload('long')` before invoking.
- **Inner classes** use `$`: `'com.example.Outer$Inner'`.
- **Signature drift across app versions.** A hardcoded overload can break after an
  update; log `.overloads.length` to confirm the shape before hardcoding, or hook
  all overloads.
- Still can't match? Enumerate the real signatures — see
  [java-enumerate.md](java-enumerate.md).
