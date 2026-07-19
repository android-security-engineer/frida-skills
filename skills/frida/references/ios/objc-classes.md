---
name: objc-classes
description: Discovering Objective-C classes and their methods on iOS/macOS via ObjC.classes, $className, $methods, $ownMethods, and $superclass, guarded by ObjC.available.
---

# ObjC.classes — find classes and their methods

**When to use:** you're on an iOS/macOS target and need the class or selector
name to hook. `ObjC.classes` is the registry of every loaded Objective-C class;
enumerate it to locate targets, then read `$methods` to find the selector.

The `ObjC` bridge only exists **inside the process on-device**. Reach the device
with `-U` and a jailbreak `frida-server` (or a re-signed `frida-gadget`), and
guard every use with `ObjC.available`.

## Shortest working example

```js
if (ObjC.available) {
  const NSString = ObjC.classes.NSString;          // a class by name
  console.log('[*] NSString superclass = ' + NSString.$superclass.$className);

  // find classes whose name matches a keyword
  for (const name in ObjC.classes) {
    if (/Login|Auth/.test(name)) console.log(name);
  }
}
```

## Inspecting a class

```js
if (ObjC.available) {
  const cls = ObjC.classes.NSURLSession;
  console.log('[*] name        = ' + cls.$className);
  console.log('[*] own methods = ' + cls.$ownMethods.join('\n'));   // declared on cls
  console.log('[*] all methods = ' + cls.$methods.length);          // incl. inherited
}
```

- `$className` — the class's name string.
- `$methods` — every method key, including inherited ones.
- `$ownMethods` — only methods declared on this class (much shorter; start here).
- `$superclass` — the superclass wrapper (`.$className` for its name).
- `$ivars` — instance variables on a live instance (see [objc-object.md](objc-object.md)).

Method keys look like `'- selWith:arg:'` (instance) or `'+ classMethod'` (class);
the leading `-`/`+` and spaces are part of the key. Pass that exact key to hook or
call the method — see [objc-method-hook.md](objc-method-hook.md).

## Searching efficiently with ApiResolver

Enumerating `ObjC.classes` by hand is fine for a keyword, but the `objc` resolver
matches selectors across all classes with one glob:

```js
if (ObjC.available) {
  const r = new ApiResolver('objc');
  for (const m of r.enumerateMatches('-[NSURLSession *dataTask*]')) {
    console.log(m.name + '  ' + m.address);   // '-[NSURLSession dataTaskWithURL:]' etc.
  }
}
```

## Pitfalls

- **Class not loaded yet.** A class from a lazily-loaded framework or plugin won't
  appear until its module loads. Trigger the app flow first, or hook early — see
  [ios-spawn-gating.md](ios-spawn-gating.md).
- **`ObjC.classes.Foo` is `undefined` if the name is wrong.** Names are
  case-sensitive and include the framework prefix (`NSURLSession`, not `URLSession`
  — the latter is Swift; see [swift-interop.md](swift-interop.md)).
- **`$methods` is large.** On `NSObject`-rooted classes it can be thousands of
  entries; prefer `$ownMethods` or `ApiResolver('objc')` to narrow down.
- **Always guard with `ObjC.available`.** On a target without the Objective-C
  runtime (a pure C or Swift-only binary), the bridge is absent and access throws.
