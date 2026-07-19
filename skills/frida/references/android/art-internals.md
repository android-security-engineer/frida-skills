---
name: art-internals
description: Reach ART internals from Frida on Android — Java.vm, getEnv, JNI RegisterNatives discovery, and when raw ArtMethod access beats the high-level Java bridge.
---

# ART internals: when the Java bridge isn't enough

**When to use:** the `Java.use`/`Java.perform` bridge covers most tasks, but some
work needs the runtime beneath it — reading a `JNIEnv`, discovering natives
registered via `RegisterNatives`, or hooking `libart.so` functions that back the
Java API. This doc is the escape hatch; prefer the bridge first
([java-use-hook.md](java-use-hook.md)).

## Getting a JNIEnv

`Java.vm` is the `JavaVM`; `getEnv()` gives a per-thread `JNIEnv` wrapper:

```js
Java.perform(() => {
  const env = Java.vm.getEnv();
  console.log('JNIEnv @', env.handle);
});
```

The wrapper exposes JNI calls: `getStringUtfChars`, `getByteArrayElements`,
`getArrayLength`, `newStringUtf`, `findClass`, `getObjectClass`, etc. Use it to
decode JNI arguments inside native hooks — see the string example in
[jni-hooks.md](jni-hooks.md). If you call JNI from a Frida-created thread, wrap
with `Java.vm.getEnv()` on that thread (it attaches as needed).

## Discovering dynamically registered natives

Apps that hide native functions behind `RegisterNatives` have no useful export
names. Hook `RegisterNatives` in `libart.so` to dump the method→pointer table:

```js
const art = Process.getModuleByName('libart.so');
// symbol is C++-mangled; resolve by pattern
const reg = art.enumerateSymbols()
  .find(s => s.name.includes('RegisterNatives') && s.name.includes('CheckJNI') === false);
Interceptor.attach(reg.address, {
  onEnter(args) {
    // args: (JNIEnv*, jclass, const JNINativeMethod*, jint nMethods)
    const methods = args[2];
    const count = args[3].toInt32();
    for (let i = 0; i < count; i++) {
      const entry = methods.add(i * Process.pointerSize * 3);
      const name = entry.readPointer().readCString();
      const sig  = entry.add(Process.pointerSize).readPointer().readCString();
      const fnPtr = entry.add(Process.pointerSize * 2).readPointer();
      console.log(`[RegisterNatives] ${name}${sig} -> ${fnPtr}`);
    }
  }
});
```

Each `JNINativeMethod` is `{ char* name; char* signature; void* fnPtr; }`, so the
stride is three pointers. Feed the resulting `fnPtr` to `Interceptor.attach`.

## Hooking libart functions directly

libart symbols are mangled; find them by substring instead of guessing:

```js
Process.getModuleByName('libart.so').enumerateSymbols()
  .filter(s => s.name.includes('LoadNativeLibrary'))
  .forEach(s => console.log(s.name, s.address));
```

Common targets: `ArtMethod::Invoke`, `ClassLinker::DefineClass`,
`JavaVMExt::LoadNativeLibrary`. Signatures differ across Android versions, so
inspect args by offset and verify on the actual device.

## Pitfalls

- **Symbol names are unstable.** Never hard-code a mangled name; match by
  substring against `enumerateSymbols()` and confirm on-device.
- **ABI/version drift.** ArtMethod layout and libart internals change every
  Android release — check with `Java.androidVersion` and test empirically.
- **Thread/JNIEnv mismatch.** A `JNIEnv` is thread-local; don't cache one across
  threads. Call `Java.vm.getEnv()` on the thread you're using.
- **Prefer the bridge.** Raw ART hooking is brittle; only drop here when
  `Java.use`/`Java.choose` genuinely can't reach the target.
