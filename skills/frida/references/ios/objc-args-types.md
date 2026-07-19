---
name: objc-args-types
description: Reading Objective-C method arguments in a Frida hook on iOS/macOS — self and _cmd, boxing pointers with ObjC.Object, decoding NSString/NSData/NSNumber and primitive scalar args.
---

# Reading selectors, self, and typed arguments

**When to use:** you've hooked an Objective-C method (see
[objc-method-hook.md](objc-method-hook.md)) and need to make sense of `args` — who
is `self`, what selector fired, and how to decode each typed argument.

Guard with `ObjC.available`; reach the device with `-U`.

## Argument layout

For any Objective-C method, `args` (all **NativePointers**) are:

| Index | Meaning |
| --- | --- |
| `args[0]` | `self` — the receiver object |
| `args[1]` | `_cmd` — the selector (a `SEL`) |
| `args[2]`, `args[3]`, … | the method's declared arguments, in order |

```js
if (ObjC.available) {
  const m = ObjC.classes.NSUserDefaults['- setObject:forKey:'];
  Interceptor.attach(m.implementation, {
    onEnter(args) {
      const self = new ObjC.Object(args[0]);
      const sel  = ObjC.selectorAsString(args[1]);     // 'setObject:forKey:'
      const value = new ObjC.Object(args[2]);
      const key   = new ObjC.Object(args[3]);
      console.log(`[*] ${self.$className} ${sel}  ${key} = ${value}`);
    }
  });
}
```

## Decoding common object types

Object arguments (`id`, `NSString*`, `NSData*`, `NSNumber*`, `NSDictionary*`…) are
pointers — wrap with `new ObjC.Object(...)` (see [objc-object.md](objc-object.md)):

```js
if (ObjC.available) {
  const data = new ObjC.Object(args[2]);               // NSData*
  console.log('[*] length = ' + data.length());
  // NSData bytes -> read raw memory through the pointer
  const bytes = data.bytes();                          // returns a NativePointer
  console.log(hexdump(bytes, { length: Math.min(64, data.length()) }));

  const str = new ObjC.Object(args[3]).toString();     // NSString* -> JS string
}
```

## Decoding scalar (non-object) arguments

Primitives are passed by value in the pointer slot — read them off the pointer, do
**not** wrap them:

```js
if (ObjC.available) {
  const asInt   = args[2].toInt32();                   // NSInteger / int
  const asUInt  = args[2].toUInt32();                  // NSUInteger
  const asBool  = !args[2].isNull();                   // BOOL: 0 = NO, else YES
  const asPtr   = args[2];                             // a raw C pointer / struct*
}
```

`double`/`float` arguments are passed in FP registers and are **not** reliably in
`args` on ARM64 — hook a wrapper that takes them as objects, or read the register
via `this.context` if you know the ABI.

## Pitfalls

- **Off-by-two.** The first real argument is `args[2]`, not `args[0]`.
- **`ObjC.selectorAsString(args[1])`** is the clean way to log the selector; don't
  try to read `_cmd` as a C string directly.
- **Scalars vs objects.** Wrapping a scalar (`new ObjC.Object(args[2])` on an
  `NSInteger`) crashes on method calls. Know the type from the selector signature.
- **Copy inside the callback.** Autoreleased objects may be gone by `onLeave`;
  stringify or `readByteArray` the data now.
- **Floating-point args** are unreliable in `args` on ARM64 — see note above.
