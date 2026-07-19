---
name: java-reflection
description: Using Java reflection through Frida to invoke private methods, read fields on unknown types, and handle inner, anonymous, and generic Android Java classes.
---

# Reflection through Frida

**When to use:** the wrapper API isn't enough — you need to enumerate members of
an unknown object, invoke a private method by name, or reach inner/anonymous
classes whose names you must discover. Frida can call `java.lang.reflect.*`
directly because those are just Java classes.

## Inspect an unknown object's real type and members

```js
Java.perform(() => {
  const Session = Java.use('com.example.Session');
  Session.login.implementation = function (u, p) {
    const r = this.login(u, p);
    const klass = this.getClass();                 // java.lang.Class
    console.log('actual class: ' + klass.getName());
    klass.getDeclaredMethods().forEach((m) => console.log(m.toString()));
    klass.getDeclaredFields().forEach((f) => console.log(f.toString()));
    return r;
  };
});
```

## Invoke a private method reflectively

```js
Java.perform(() => {
  const obj = /* a live instance, e.g. from Java.choose */ null;
  if (obj !== null) {
    const m = obj.getClass().getDeclaredMethod('computeSecret', []);
    m.setAccessible(true);
    const secret = m.invoke(obj, []);              // returns java.lang.Object
    console.log('secret = ' + secret);
  }
});
```

For methods with parameters, pass a `Class[]` of parameter types and an
`Object[]` of arguments — build them via `Java.use('java.lang.Class')` lookups and
`Java.array('java.lang.Object', [...])`.

## Read a private field reflectively

```js
Java.perform(() => {
  const obj = null; // some instance
  if (obj !== null) {
    const f = obj.getClass().getDeclaredField('apiKey');
    f.setAccessible(true);
    console.log('apiKey = ' + f.get(obj));
  }
});
```

Usually the direct `.value` accessor (see [java-fields.md](java-fields.md)) is
simpler; reflection wins when the declaring type is unknown or synthetic.

## Inner, anonymous, and generic classes

- **Inner/nested** classes use `$`: `Java.use('com.example.Outer$Inner')`.
- **Anonymous** classes are `Outer$1`, `Outer$2`… — discover the exact suffix with
  [java-enumerate.md](java-enumerate.md) or `klass.getName()` in a hook.
- **Generics** are erased at runtime; hook the raw type (e.g. `java.util.List`)
  and inspect elements' actual classes via `getClass()`.

## Pitfalls

- **Forgetting `setAccessible(true)`** before invoking/reading a private member
  throws `IllegalAccessException`.
- **`getMethod` vs `getDeclaredMethod`.** `getDeclaredMethod` finds private and
  package methods on that class only; `getMethod` finds public ones including
  inherited. Pick accordingly.
- **Parameter-type arrays must match exactly**, using boxed classes for the lookup
  but primitives at call time — mismatches throw `NoSuchMethodException`.
- **Reflection is slower**; in hot hooks prefer direct wrapper calls or
  `.overload(...)`.
- **Class not loaded** for `$`-named inner classes → resolve the loader first,
  see [java-classloaders.md](java-classloaders.md).
