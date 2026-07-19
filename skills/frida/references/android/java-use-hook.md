---
name: java-use-hook
description: How to hook an Android Java method with Java.use and .implementation, call the original, read/modify arguments and return values, and revert.
---

# Java.use and replacing .implementation

**When to use:** you want to observe or change what a specific Java method does —
log its arguments, alter its return, or block it entirely.

## Shortest working example

```js
Java.perform(() => {
  const Log = Java.use('android.util.Log');
  Log.d.overload('java.lang.String', 'java.lang.String').implementation =
    function (tag, msg) {
      console.log('[Log.d] ' + tag + ': ' + msg);
      return this.d(tag, msg);          // call the original, keep behavior
    };
});
```

Load it against a reachable device (`-U`, matching `frida-server` or gadget):

```sh
frida -U -n com.example.app -l agent.js -q
```

## The pattern

1. `const C = Java.use('fully.qualified.ClassName')` returns a **wrapper class**.
2. `C.methodName` is the method wrapper. Assign a function to its
   `.implementation` to replace the body.
3. Inside the replacement, `this` is the receiver instance. **Call the original**
   via `this.methodName(...)` with the same wrapper — do not recurse into your own
   closure. The return value you give back is what the caller sees.

Modify inputs or outputs freely:

```js
Java.perform(() => {
  const Checker = Java.use('com.example.LicenseChecker');
  Checker.isValid.implementation = function () {
    const real = this.isValid();          // original result
    console.log('[*] isValid real=' + real + ' -> forcing true');
    return true;                          // override
  };
});
```

Static methods work the same way; there is no instance, but `this` still refers to
the class wrapper, so `this.method(...)` calls the original.

## Reverting a hook

Restore the original implementation by assigning `null`:

```js
Checker.isValid.implementation = null;
```

## Pitfalls

- **Overloaded methods.** If a method has multiple signatures, assigning
  `.implementation` directly throws an "overload" error. Pick one with
  `.overload('int', 'java.lang.String')` first — see
  [java-overloads.md](java-overloads.md).
- **Argument types are wrappers.** A `String` arg is a Java String wrapper; use
  it directly in `console.log` (it stringifies) but `.toString()` when in doubt.
  For arrays/objects see [java-cast-array.md](java-cast-array.md).
- **Returning the wrong type.** Return a value matching the method's declared
  return type. Returning `undefined` from a non-void method breaks the caller.
- **Calling the original with wrong receiver.** Use `this.method(...)`, not
  `C.method(...)`, for instance methods — the latter has no `this`.
- **Class not loaded yet** → `ClassNotFoundException`. Hook after the owning
  classloader has defined it; see [java-classloaders.md](java-classloaders.md).
- **Hooking too late.** If the app already ran the code once at startup, spawn it
  under instrumentation instead of attaching — see [spawn-gating.md](spawn-gating.md).
