---
name: java-enumerate
description: Discovering what to hook on Android with Java.enumerateLoadedClasses and enumerateMethods, filtering by package or name to find target classes and methods.
---

# Enumerating classes and methods

**When to use:** you don't yet know the exact class or method name to hook.
Enumerate the loaded classes, filter by package or keyword, then list a class's
methods to get precise signatures.

## List loaded classes matching a keyword

```js
Java.perform(() => {
  Java.enumerateLoadedClasses({
    onMatch: (name /*, handle */) => {
      if (name.toLowerCase().includes('crypto') ||
          name.startsWith('com.example.')) {
        console.log(name);
      }
    },
    onComplete: () => console.log('[*] class scan done'),
  });
});
```

A synchronous variant returns an array — handy for one-off filtering:

```js
Java.perform(() => {
  const hits = Java.enumerateLoadedClassesSync()
    .filter((n) => n.includes('LoginManager'));
  console.log(JSON.stringify(hits, null, 2));
});
```

## List a class's methods and signatures

Use ART's `getDeclaredMethods` via reflection to see exact overloads to feed into
`.overload(...)`:

```js
Java.perform(() => {
  const cls = Java.use('com.example.LoginManager');
  const methods = cls.class.getDeclaredMethods();
  methods.forEach((m) => console.log(m.toString()));
  const fields = cls.class.getDeclaredFields();
  fields.forEach((f) => console.log(f.toString()));
});
```

Each `Method.toString()` prints modifiers, return type, and parameter types — the
signature you translate into an `.overload(...)` call
(see [java-overloads.md](java-overloads.md)).

## From the CLI

`frida-trace` can auto-discover and stub Java methods by glob, generating handlers
you then edit:

```sh
frida-trace -U -f com.example.app -j 'com.example.*!*'
```

## Pitfalls

- **Only *loaded* classes appear.** `enumerateLoadedClasses` misses classes not
  yet defined — dynamically loaded DEX, lazily initialized SDKs. Trigger the app
  feature first, or hook the classloader; see
  [java-classloaders.md](java-classloaders.md).
- **Huge output.** On a real app the class list is thousands of entries. Always
  filter inside `onMatch` (or on the `...Sync` array) rather than logging all.
- **Multiple classloaders.** A class may exist in a child loader not searched by
  default `Java.use`. Enumerate loaders too — see
  [java-classloaders.md](java-classloaders.md).
- **Method list needs `.class`.** Use `cls.class.getDeclaredMethods()` (the real
  `java.lang.Class`), not the Frida wrapper, for reflection.
- **Timing.** Enumerating at agent load (before the app runs) shows only
  framework classes. Do it after the relevant screen/feature has been exercised,
  or spawn-gate — see [spawn-gating.md](spawn-gating.md).
