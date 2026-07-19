---
name: java-fields
description: Reading and writing Android Java instance and static fields through the .value accessor, handling name clashes with methods via the _name form.
---

# Fields: reading and writing .value

**When to use:** you need the state inside an object — a private token, a boolean
flag, a static config — or you want to overwrite it. Fields are exposed on the
wrapper, and you read/write the actual value through **`.value`**.

## Shortest working example

```js
Java.perform(() => {
  // static field
  const BuildConfig = Java.use('com.example.app.BuildConfig');
  console.log('DEBUG = ' + BuildConfig.DEBUG.value);
  BuildConfig.DEBUG.value = true;        // overwrite the static

  // instance field, from within a hook where `this` is the object
  const Session = Java.use('com.example.Session');
  Session.authenticate.implementation = function (user, pass) {
    const r = this.authenticate(user, pass);
    console.log('token=' + this.token.value);   // read private instance field
    this.token.value = 'forged';                // write it
    return r;
  };
});
```

## The rules

- A field is a **holder object**; the value is behind `.value`. Reading
  `obj.field` alone gives the holder, not the value.
- Works for `private`/`protected` fields — Frida ignores Java access control.
- **Static fields** are read/written on the `Java.use(...)` wrapper directly.
  **Instance fields** need an instance: `this` inside a hook, or an object from
  `$new` / [java-choose.md](java-choose.md).
- Assigning `.value` must match the field type: primitives as JS numbers/booleans,
  objects as Java wrappers, arrays via `Java.array(...)`.

## Name clashes between a field and a method

If a class has a field and a method with the **same name**, the method wins on the
bare wrapper. Access the field with a leading underscore:

```js
Java.perform(() => {
  const obj = /* ... some instance ... */ null;
  // if `count` is both a field and a method name:
  // console.log(obj._count.value);   // the field
  // obj.count();                     // the method
});
```

Frida prints the underscored alias in error messages when a clash exists.

## Pitfalls

- **Forgetting `.value`.** `obj.token` is the holder; `obj.token.value` is the
  data. Writing `obj.token = x` does nothing useful.
- **Reading an instance field with no instance.** Static access on a wrapper only
  reaches static fields; for instance fields you need `this` or a chosen object.
- **Type mismatch on write.** Assigning a JS string to an `int` field, or a raw
  JS array where a `[B` is expected, throws. Convert first —
  [java-cast-array.md](java-cast-array.md).
- **Field not visible** because you cast to the wrong class. Use
  [java-cast-array.md](java-cast-array.md) (`Java.cast`) to view the object as the
  class that actually declares the field.
- **Timing.** Reading a field before the app has populated it yields the default
  (null/0). Hook the setter or read it later in the lifecycle.
