---
name: java-constructors
description: Hooking Android Java constructors via $init, instantiating objects with $new, and disposing wrappers with $dispose, including overloaded constructors.
---

# Constructors: $init, $new, $dispose

**When to use:** you want to observe objects as they are built (hook `$init`),
or create Java objects yourself from the agent (`$new`) to pass into other hooks
or call methods on.

## Hooking a constructor with $init

`$init` is the method wrapper for a class's constructor(s). Hook it like any
method; it is almost always overloaded, so pick the signature.

```js
Java.perform(() => {
  const URL = Java.use('java.net.URL');
  URL.$init.overload('java.lang.String').implementation = function (spec) {
    console.log('[new URL] ' + spec);
    return this.$init(spec);            // run the real constructor
  };
});
```

**Always call `this.$init(...)`** for the original — skipping it leaves the object
half-constructed.

## Creating an object with $new

`$new` allocates and constructs a fresh instance from the agent. Use the same
overload rules as methods.

```js
Java.perform(() => {
  const String = Java.use('java.lang.String');
  const s = String.$new('hello from frida');
  console.log(s.length());              // 17

  const File = Java.use('java.io.File');
  const f = File.$new('/data/local/tmp/x');
  console.log('exists=' + f.exists());
});
```

`$new` respects overloads:

```js
Java.perform(() => {
  const Integer = Java.use('java.lang.Integer');
  const boxed = Integer.$new.overload('int').call(Integer, 42);
  console.log(boxed.intValue());
});
```

## Freeing a wrapper with $dispose

Java wrappers hold a JNI global reference. Frida garbage-collects them, but in
tight loops (e.g. inside a hot hook creating many `$new` objects) you can release
eagerly:

```js
const tmp = Java.use('java.lang.StringBuilder').$new();
// ... use tmp ...
tmp.$dispose();                          // drop the JNI ref now
```

## Pitfalls

- **Forgetting `this.$init(...)`** in an `$init` hook leaves the instance
  uninitialized and usually crashes the app later.
- **Overload errors on `$init`/`$new`** — constructors are frequently overloaded;
  select with `.overload('int', 'java.lang.String')`. See
  [java-overloads.md](java-overloads.md).
- **Wrong argument wrapper types.** Pass primitives as JS numbers/booleans; pass
  objects as Java wrappers (from another `Java.use`/`$new`), not raw JS objects.
  For arrays use `Java.array(...)` — see [java-cast-array.md](java-cast-array.md).
- **`$new` on an abstract class or interface** throws. Instead implement it with
  [java-registerclass.md](java-registerclass.md) or find a concrete subclass.
- **Class not yet loaded** → `ClassNotFoundException`; see
  [java-classloaders.md](java-classloaders.md).
