---
name: objc-object
description: Wrapping a raw pointer as an Objective-C object with ObjC.Object(ptr) on iOS/macOS to call methods, read properties/ivars, and stringify it, guarded by ObjC.available.
---

# ObjC.Object — use a pointer as an Objective-C object

**When to use:** a hook handed you a raw pointer (a `NativePointer` in `args`,
`retval`, or an ivar) and you want to *use* it as the real object — call its
methods, read its properties, or print it. `ObjC.Object(ptr)` builds a live
wrapper.

Guard with `ObjC.available`; reach the device with `-U`.

## Shortest working example

```js
if (ObjC.available) {
  Interceptor.attach(ObjC.classes.NSURL['- initWithString:'].implementation, {
    onEnter(args) {
      const str = new ObjC.Object(args[2]);          // args[2] is an NSString*
      console.log('[*] initWithString: ' + str.toString());
      console.log('[*] class = ' + str.$className);
    }
  });
}
```

`new ObjC.Object(ptr)` and `ObjC.Object(ptr)` are equivalent. The wrapper exposes
the object's methods as JS functions and its class metadata as `$`-properties.

## Calling methods and reading state

```js
if (ObjC.available) {
  const dict = ObjC.classes.NSMutableDictionary.dictionary();   // a live instance
  dict.setObject_forKey_(ObjC.classes.NSString.stringWithString_('v'),
                         ObjC.classes.NSString.stringWithString_('k'));

  console.log('[*] count      = ' + dict.count());              // call method
  console.log('[*] value      = ' + dict.objectForKey_('k'));   // colons -> underscores
  console.log('[*] description= ' + dict.toString());           // -description
  console.log('[*] className  = ' + dict.$className);
  console.log('[*] ivars      = ' + JSON.stringify(dict.$ivars));
}
```

- **Selectors → JS methods:** each `:` becomes `_`. `setObject:forKey:` is called
  as `.setObject_forKey_(a, b)`. A no-argument `count` is `.count()`.
- **`toString()`** invokes `-description` — great for logging.
- **`$className`, `$class`, `$superclass`, `$ivars`, `$methods`** inspect the object.
- **`.handle`** is the underlying NativePointer (pass it back to native code).

## Boxing JS values into objects

```js
if (ObjC.available) {
  const s = ObjC.classes.NSString.stringWithString_('hello');   // JS string arg auto-boxes
  const n = ObjC.classes.NSNumber.numberWithInt_(42);
  console.log(s.length() + ' / ' + n.intValue());
}
```

JS strings passed to a method expecting `NSString*` are boxed automatically. To
turn an object *back* into a JS string, call `.toString()`.

## Pitfalls

- **Nil pointers.** `new ObjC.Object(NULL)` or wrapping a zero pointer is invalid —
  check `args[2].isNull()` first.
- **Not every pointer is an object.** Wrapping an arbitrary C pointer yields a
  wrapper that crashes on method calls. Only wrap pointers you know are `id`s.
- **Wrong ownership after the call returns.** A wrapped autoreleased object may be
  freed after `onLeave`; don't stash the wrapper for later — copy the data you need
  (e.g. `.toString()`) inside the callback.
- **Selector spelling.** `objectForKey:` → `.objectForKey_` (trailing underscore
  for the trailing colon). Missing the final `_` is a common error.
