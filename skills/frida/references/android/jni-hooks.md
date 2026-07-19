---
name: jni-hooks
description: Hook native .so functions and JNI entry points on Android with Interceptor, resolving exports and JNIEnv-based calls when logic lives in C/C++ instead of Java.
---

# Hooking native code and JNI on Android

**When to use:** the interesting logic is in a `.so` (obfuscation, crypto,
license, root checks moved to native to dodge the Java bridge). The Java bridge
can't see it — you hook the native function directly with `Interceptor`.

## Shortest working example — hook an exported native function

```js
const lib = Process.getModuleByName('libnative-lib.so');
const fn = lib.getExportByName('Java_com_example_app_Crypto_encrypt');
Interceptor.attach(fn, {
  onEnter(args) {
    // JNI natives: args[0]=JNIEnv*, args[1]=jobject/jclass, then declared args
    console.log('[encrypt] called from', this.returnAddress);
  },
  onLeave(retval) {
    console.log('[encrypt] returned', retval);
  }
});
```

`args[i]` and `retval` are NativePointers — read through them (see the memory
rules in [../core-api/index.md](../core-api/index.md)).

## Waiting for the library to load

At spawn time the `.so` may not be mapped yet. Either gate on the loader (see
[system-loadlibrary.md](system-loadlibrary.md)) or poll:

```js
function withModule(name, cb) {
  const m = Process.findModuleByName(name);
  if (m) { cb(m); return; }
  const iv = setInterval(() => {
    const m2 = Process.findModuleByName(name);
    if (m2) { clearInterval(iv); cb(m2); }
  }, 50);
}
withModule('libnative-lib.so', lib => {
  Interceptor.attach(lib.getExportByName('check_license'), {
    onLeave(retval) { retval.replace(ptr(1)); }   // force success
  });
});
```

## Reading JNI string arguments

A `jstring` is an opaque pointer; convert it via the JNI API rather than reading
it directly. Use `Java.vm` to reach a `JNIEnv`:

```js
Java.perform(() => {
  const lib = Process.getModuleByName('libnative-lib.so');
  Interceptor.attach(lib.getExportByName('Java_com_example_app_Auth_verify'), {
    onEnter(args) {
      const env = Java.vm.getEnv();
      const str = env.getStringUtfChars(args[2], NULL).readUtf8String();
      console.log('[verify] password =', str);
    }
  });
});
```

`Java.vm.getEnv()` returns a wrapper exposing `getStringUtfChars`,
`getArrayLength`, `getByteArrayElements`, etc. Guard the whole thing with
`Java.available`.

## Non-exported / static functions

If the target isn't an export, resolve it by offset from the module base or by
scanning:

```js
const base = Process.getModuleByName('libnative-lib.so').base;
Interceptor.attach(base.add(0x00012a40), { onEnter(args) { /* ... */ } });
```

Find offsets with `enumerateSymbols()`, `DebugSymbol.fromAddress`, or an
`ApiResolver('module')`. On ARM64 a Thumb/exact address matters only for
`Interceptor.replace` with a hand-written stub.

## Pitfalls

- **JNI arg indexing.** For `Java_*` functions, the first two args are always
  `JNIEnv*` and the `jobject`/`jclass`; your declared parameters start at
  `args[2]`.
- **Wrong ABI.** A 64-bit device loads the arm64 `.so`; a `.so` name that exists
  in multiple ABIs still resolves per-process to the loaded one.
- **Hooking too early.** Attaching before the lib is mapped throws "module not
  found" — poll or gate on the loader ([system-loadlibrary.md](system-loadlibrary.md)).
- **RegisterNatives.** Dynamically registered natives have mangled/unknown export
  names; hook `RegisterNatives` in `libart.so` to discover their function
  pointers — see [art-internals.md](art-internals.md).
