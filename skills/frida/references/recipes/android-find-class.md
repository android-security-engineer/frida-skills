---
name: android-find-class
description: Frida agent that searches loaded Android Java classes and their methods by regex at runtime to discover the exact class or method name to hook.
---

# Find a Java class / method by regex at runtime

**When:** you need to hook something but don't know its fully-qualified name.
Enumerate loaded classes, filter by pattern, then list a candidate's methods.
Java bridge only — runs on-device via `frida-server`.

```js
// recipe.js — list loaded classes matching a regex.
const NEEDLE = /login|auth|token|crypt/i;   // change to your keyword

if (Java.available) {
  Java.perform(function () {
    const seen = [];
    Java.enumerateLoadedClasses({
      onMatch(name) { if (NEEDLE.test(name)) seen.push(name); },
      onComplete() {
        seen.sort();
        seen.forEach(n => console.log(n));
        console.log(`[*] ${seen.length} matches`);
      },
    });
  });
} else {
  console.log('[-] Java runtime not available (Android only)');
}
```

Found a class? List its methods and fields to pick the hook target:

```js
// recipe-methods.js — dump declared methods of one class.
Java.perform(function () {
  const cls = 'com.example.app.AuthManager';        // from the search above
  const C = Java.use(cls);
  // getDeclaredMethods() returns java.lang.reflect.Method[] — print each signature.
  C.class.getDeclaredMethods().forEach(m => console.log(m.toString()));
  console.log('--- fields ---');
  C.class.getDeclaredFields().forEach(f => console.log(f.toString()));
});
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -U -n com.example.app -l recipe.js      # attach to running app
```

**Tweak this:**
- A class loaded lazily won't appear until used — attach after triggering the
  feature, or spawn and drive the app to the relevant screen first.
- Multiple classloaders (plugins, DexClassLoader)? Use
  `Java.enumerateClassLoaders({onMatch, onComplete})` and `Java.classFactory` to
  target the right loader.
- Want *live instances* and their field values, not just the class? Use
  `Java.choose('com.example.app.AuthManager', { onMatch(inst){…}, onComplete(){} })`.
- Ready to hook? Set `.implementation` on an overload — see
  [android-crypto-capture.md](android-crypto-capture.md).
