---
name: objc-replace-implement
description: Replacing an Objective-C method body on iOS/macOS by assigning method.implementation = ObjC.implement(method, fn), with access to the original IMP for pass-through.
---

# Replace an Objective-C implementation

**When to use:** you want to *substitute* a method's behaviour — return a fixed
value, skip a check, or wrap the original — rather than merely observe it (that's
[objc-method-hook.md](objc-method-hook.md)). Assign a new IMP built with
`ObjC.implement`.

Guard with `ObjC.available`; reach the device with `-U`.

## Shortest working example

```js
if (ObjC.available) {
  const m = ObjC.classes.NSString['- isEqualToString:'];
  const original = m.implementation;                 // keep the old IMP to call through

  m.implementation = ObjC.implement(m, function (self, sel, other) {
    // self, sel are NativePointers; extra args follow (here: `other`)
    const result = new NativeFunction(original, 'bool', ['pointer', 'pointer', 'pointer'])(self, sel, other);
    console.log('[*] isEqualToString: -> ' + result);
    return result ? 1 : 0;                            // BOOL as 0/1
  });
}
```

`ObjC.implement(method, fn)` compiles `fn` into a native IMP with the method's
signature. The callback receives `self`, `_cmd`, then the real arguments — all
**NativePointers**. Return a value matching the method's return type (a pointer,
or `0`/`1` for `BOOL`).

## Force a return value (skip the real work)

```js
if (ObjC.available) {
  // Pretend a jailbreak check always says "clean"
  const m = ObjC.classes.SecurityManager['- isDeviceJailbroken'];
  m.implementation = ObjC.implement(m, () => 0);     // always NO
}
```

## Calling the original from the replacement

Wrap the saved `original` pointer in a `NativeFunction` whose types match the
selector (see [objc-args-types.md](objc-args-types.md) for mapping selector types
to Frida types), call it, then post-process — as in the first example.

## Pitfalls

- **Signature must match.** `ObjC.implement` reads the method's type encoding, but
  your `return` must fit it. Returning a JS string where an `id` is expected won't
  auto-box — return an `ObjC.Object`'s `.handle`, or an allocated `NSString`.
- **Global effect.** Replacing an IMP changes it for *every* instance and caller,
  not just one object. For per-object logic, branch on `self` inside `fn`.
- **Save the original before assigning.** Read `m.implementation` first; once
  overwritten you can't recover it except via `Interceptor.revert` (which only
  applies if you used `Interceptor.replace` instead).
- **Prefer `Interceptor.attach`** ([objc-method-hook.md](objc-method-hook.md)) when
  you only need to peek or tweak `retval` — it's simpler and reversible with
  `Interceptor.revert`.
- **Authorization.** Overriding a security check is a bypass — only on software you
  are authorized to analyze.
