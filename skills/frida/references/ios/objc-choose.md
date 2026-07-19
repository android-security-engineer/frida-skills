---
name: objc-choose
description: Enumerating live Objective-C instances of a class on iOS/macOS with ObjC.choose to inspect or drive already-constructed objects you cannot obtain through a hook.
---

# ObjC.choose — grab live instances off the heap

**When to use:** the object you care about already exists (a live
`NSURLSession`, a logged-in session model, a decrypted config) and no hook hands
it to you. `ObjC.choose` scans the heap for instances of a class and gives you each
one as a usable `ObjC.Object`.

Guard with `ObjC.available`; reach the device with `-U`.

## Shortest working example

```js
if (ObjC.available) {
  ObjC.choose(ObjC.classes.NSURLSession, {
    onMatch(session) {
      // session is a live ObjC.Object
      console.log('[*] session @ ' + session.handle + '  ' + session.$className);
    },
    onComplete() {
      console.log('[*] scan complete');
    }
  });
}
```

Each `onMatch` argument is a fully usable wrapper: call its methods, read
properties/ivars (see [objc-object.md](objc-object.md)), or pass it elsewhere.

## Reading and driving a live object

```js
if (ObjC.available) {
  ObjC.choose(ObjC.classes.AppSession, {
    onMatch(s) {
      console.log('[*] token = ' + s.authToken());     // read private state
      s.setLoggedIn_(1);                                 // drive the live object
      return 'stop';                                     // stop after the first
    },
    onComplete() {}
  });
}
```

Return the string `'stop'` from `onMatch` to end the scan early once you have what
you need.

## Pitfalls

- **Only currently-existing instances** are found. If the object hasn't been
  created yet, `onMatch` never fires — trigger the app flow first, or hook the
  initializer (`-init…`) via [objc-method-hook.md](objc-method-hook.md) to catch it
  at creation time.
- **Pass the class object, not a string.** `ObjC.choose(ObjC.classes.Foo, ...)`,
  not `ObjC.choose('Foo', ...)`.
- **Exact class matching.** Choosing a base class does not automatically include
  every subclass instance in a useful way; choose the concrete class you saw in
  [objc-classes.md](objc-classes.md).
- **Cost.** A full heap scan is expensive on a large app; scope it to one class and
  don't run it in a tight loop.
- **Threading & lifetime.** `onMatch` runs synchronously during the scan; keep work
  short, and copy out any data (`.toString()`, `readByteArray`) rather than stashing
  the wrapper for later.
