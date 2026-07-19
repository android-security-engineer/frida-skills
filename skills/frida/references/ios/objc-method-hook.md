---
name: objc-method-hook
description: Hooking an Objective-C method on iOS/macOS by attaching Interceptor to the method's .implementation, reading self/_cmd/args in onEnter and the return in onLeave.
---

# Hook an Objective-C method

**When to use:** you want to observe or tweak calls to a specific Objective-C
method — log its arguments, see its return value, or change behaviour without
replacing the whole implementation. Attach `Interceptor` to the method's
`.implementation` pointer.

Guard with `ObjC.available`; reach the device with `-U` (jailbreak `frida-server`
or re-signed `frida-gadget`).

## Shortest working example

```js
if (ObjC.available) {
  const m = ObjC.classes.NSString['- isEqualToString:'];   // exact method key
  Interceptor.attach(m.implementation, {
    onEnter(args) {
      // args[0]=self, args[1]=_cmd (the selector), args[2..]=method arguments
      this.other = new ObjC.Object(args[2]).toString();
    },
    onLeave(retval) {
      console.log('[*] isEqualToString:"' + this.other + '" => ' + retval);
    }
  });
}
```

`args` are **NativePointers**. For an Objective-C method, `args[0]` is `self`,
`args[1]` is `_cmd` (the selector), and the real arguments start at `args[2]`.
Wrap object pointers with `ObjC.Object(...)` to read them — see
[objc-object.md](objc-object.md) and [objc-args-types.md](objc-args-types.md).

## Class methods and modifying the return

```js
if (ObjC.available) {
  // '+' key = class method
  const open = ObjC.classes.UIApplication['- openURL:'];
  Interceptor.attach(open.implementation, {
    onEnter(args) {
      const url = new ObjC.Object(args[2]);
      console.log('[*] openURL: ' + url.absoluteString().toString());
    },
    onLeave(retval) {
      retval.replace(ptr(1));            // force BOOL YES
    }
  });
}
```

`retval` is a NativePointer; `retval.replace(x)` overwrites the returned value. A
`BOOL` return is `ptr(0)` (NO) or `ptr(1)` (YES).

## Pitfalls

- **Attach to `.implementation`, not the method wrapper.** `Interceptor.attach(m,
  ...)` throws — you must pass `m.implementation`.
- **Argument indices shift by two.** Forgetting `self`/`_cmd` and reading `args[0]`
  as the first real argument is the most common mistake.
- **Shared implementations.** Many selectors map to one IMP; you may see calls from
  unrelated classes. Filter on `new ObjC.Object(args[0]).$className` if needed.
- **Method not found → `undefined`.** Check the exact key (leading `- `/`+ `, all
  colons) via `$ownMethods` in [objc-classes.md](objc-classes.md).
- **To *replace* the body** rather than wrap it, use
  [objc-replace-implement.md](objc-replace-implement.md) instead.
- **Early enough?** If the method runs at launch (e.g. a check in
  `application:didFinishLaunchingWithOptions:`), spawn-gate first —
  [ios-spawn-gating.md](ios-spawn-gating.md).
