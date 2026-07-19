---
name: java-classloaders
description: Hooking Android classes in non-default classloaders — enumerate loaders with Java.enumerateClassLoaders, use Java.ClassFactory, and load DEX classes not found by Java.use.
---

# Multiple classloaders and dynamically loaded classes

**When to use:** `Java.use('the.Class')` throws `ClassNotFoundException` even
though you know the class exists. The class lives in a **child classloader** (a
plugin, a packed/protected app, a dynamically loaded DEX) that Frida's default
loader doesn't search.

## Find the loader that has your class

```js
Java.perform(() => {
  const target = 'com.example.secret.Payload';
  Java.enumerateClassLoaders({
    onMatch: (loader) => {
      try {
        loader.findClass(target);        // throws if this loader lacks it
        console.log('[*] found in loader: ' + loader);
      } catch (_) { /* not here */ }
    },
    onComplete: () => console.log('[*] loader scan done'),
  });
});
```

## Bind Frida's factory to that loader, then use the class

Once you have the right loader, point a class factory at it so `.use` resolves:

```js
Java.perform(() => {
  const target = 'com.example.secret.Payload';
  Java.enumerateClassLoaders({
    onMatch: (loader) => {
      try {
        loader.findClass(target);
        Java.classFactory.loader = loader;      // switch default resolution
        const Payload = Java.use(target);       // now works
        Payload.decrypt.implementation = function (x) {
          const out = this.decrypt(x);
          console.log('[decrypt] ' + out);
          return out;
        };
      } catch (_) { /* keep scanning */ }
    },
    onComplete: () => {},
  });
});
```

Prefer a **dedicated factory** when you must juggle several loaders, leaving the
global one untouched:

```js
Java.perform(() => {
  const factory = Java.ClassFactory.get(someLoader);
  const C = factory.use('com.example.secret.Payload');
});
```

## Loading classes from a DEX/JAR file

If you have the bytecode on disk, load it directly:

```js
Java.perform(() => {
  Java.openClassFile('/data/local/tmp/patch.dex').load();
  const Helper = Java.use('com.example.patch.Helper');   // now resolvable
});
```

## Pitfalls

- **The loader isn't ready at agent load.** Child loaders are often created after
  startup (on first feature use, after unpacking). Enumerate/hook *after* the app
  has reached the relevant screen, or hook `dalvik.system.DexClassLoader.$init` /
  `System.loadLibrary` to catch creation — see
  [early-instrumentation.md](early-instrumentation.md) and
  [system-loadlibrary.md](system-loadlibrary.md).
- **Setting `Java.classFactory.loader` globally** changes resolution for all later
  `Java.use` calls. Use `Java.ClassFactory.get(loader)` for isolation when in doubt.
- **`enumerateClassLoaders` also needs `Java.perform`** and only lists loaders
  that currently exist.
- **Packed/DRM apps** may recreate or hide loaders; you may need to hook the
  packer's load routine and enumerate again afterward.
