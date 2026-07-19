---
name: java-choose
description: Grabbing live Android Java instances off the ART heap with Java.choose to inspect or drive already-constructed objects you cannot obtain via a hook.
---

# Java.choose — grab live instances off the heap

**When to use:** the object you care about already exists (a live `OkHttpClient`,
a session, a decrypted config) and you have no hook that hands it to you.
`Java.choose` scans the heap for instances of a class and gives you each one.

## Shortest working example

```js
Java.perform(() => {
  Java.choose('com.example.Session', {
    onMatch: (inst) => {
      console.log('[*] session token=' + inst.token.value);
      inst.setLoggedIn(true);            // call a method on the live object
    },
    onComplete: () => console.log('[*] heap scan complete'),
  });
});
```

Each `inst` in `onMatch` is a fully usable wrapper: read/write its fields
(`.value`), call its methods, or pass it into other code.

## Typical uses

- **Read private state** of an object created before you attached.
- **Reconfigure a live object**, e.g. relax an already-built HTTP client:

```js
Java.perform(() => {
  Java.choose('okhttp3.OkHttpClient', {
    onMatch: (client) => console.log('[*] found OkHttpClient @ ' + client),
    onComplete: () => {},
  });
});
```

- **Recover a decrypted value** that only lives in memory after login.

Return the string `'stop'` from `onMatch` to end the scan early once you have what
you need.

## Pitfalls

- **Only instances that currently exist** are found. If the object hasn't been
  created yet, `onMatch` never fires — trigger the app flow first, or hook the
  constructor (`$init`, see [java-constructors.md](java-constructors.md)) to catch
  it at creation time instead.
- **Exact class only by default.** `Java.choose('Base')` finds `Base` instances;
  subclasses are separate types. Choose the concrete class you saw in
  [java-enumerate.md](java-enumerate.md), or choose each subclass.
- **Cost.** A full heap scan is expensive on a large app; scope it to one class
  and avoid running it in a tight loop.
- **Interface/abstract targets** yield nothing directly — choose a concrete
  implementing class instead.
- **Wrong classloader.** If the class lives in a non-default loader, plain
  `Java.choose` may miss it; use the loader-aware factory from
  [java-classloaders.md](java-classloaders.md).
- **Threading.** `onMatch` runs on a VM-attached thread inside `Java.perform`;
  keep work short and don't block the app's main thread.
