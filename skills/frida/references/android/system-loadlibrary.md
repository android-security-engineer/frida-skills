---
name: system-loadlibrary
description: Catch System.loadLibrary / dlopen on Android so a native .so can be hooked the instant it is mapped, solving the "module not found" timing problem for JNI hooks.
---

# Hook a native library as it loads

**When to use:** you want to `Interceptor.attach` inside a `.so`, but at spawn
time it isn't mapped yet, so `Process.getModuleByName` throws. Hook the loader,
then install your native hooks in its `onLeave` — the library is guaranteed
present by then.

## Shortest working example — gate on System.loadLibrary

```js
Java.perform(() => {
  const System = Java.use('java.lang.System');
  System.loadLibrary.implementation = function (name) {
    this.loadLibrary(name);                    // let it actually load
    if (name === 'native-lib') {
      const lib = Process.getModuleByName('libnative-lib.so');
      Interceptor.attach(lib.getExportByName('check_license'), {
        onLeave(retval) { retval.replace(ptr(1)); }
      });
      console.log('[*] hooked libnative-lib.so after load');
    }
    return;
  };
});
```

`System.loadLibrary('native-lib')` maps `libnative-lib.so` — note the `lib`
prefix and `.so` suffix are added by the runtime, so hook the base name.

## Also cover System.load and Runtime

Some apps use the full-path variants. Hook both plus `Runtime.loadLibrary0`:

```js
Java.perform(() => {
  const Runtime = Java.use('java.lang.Runtime');
  Runtime.loadLibrary0.overload('java.lang.Class', 'java.lang.String')
    .implementation = function (cls, name) {
      this.loadLibrary0(cls, name);
      console.log('[loadLibrary0]', name);
    };
});
```

## Native-level gate — hook dlopen

To catch libraries loaded from native code (or to be language-agnostic), hook
`dlopen`/`android_dlopen_ext` in the linker:

```js
const libdl = Process.getModuleByName('libdl.so');
const dlopen = libdl.getExportByName('android_dlopen_ext');
Interceptor.attach(dlopen, {
  onEnter(args) { this.path = args[0].readUtf8String(); },
  onLeave(retval) {
    if (this.path && this.path.includes('libnative-lib.so')) {
      const lib = Process.getModuleByName('libnative-lib.so');
      Interceptor.attach(lib.getExportByName('check_license'), {
        onLeave(r) { r.replace(ptr(1)); }
      });
    }
  }
});
```

On older devices the symbol may be plain `dlopen`; try
`Module.getGlobalExportByName('android_dlopen_ext')` and fall back to `dlopen`.

## Pitfalls

- **Install hooks in `onLeave`, not `onEnter`.** In `onEnter` the mapping isn't
  complete; `getExportByName` still fails.
- **Name matching.** `System.loadLibrary('foo')` → module `libfoo.so`. Compare the
  right form on each side.
- **Must spawn.** Attaching after startup means the load already happened; use
  spawn gating ([spawn-gating.md](spawn-gating.md)) so the loader hook is armed
  first.
- **JNI_OnLoad runs before your onLeave returns control?** No — `dlopen`/
  `loadLibrary` return after `JNI_OnLoad`, so if the check runs *inside*
  `JNI_OnLoad` you're still slightly late; hook the export directly and force its
  result. See [jni-hooks.md](jni-hooks.md).
