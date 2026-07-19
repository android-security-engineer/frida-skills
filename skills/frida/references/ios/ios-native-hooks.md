---
name: ios-native-hooks
description: Hooking C and dyld functions on iOS/macOS with Interceptor by resolving exports from libSystem.B.dylib or Module.getGlobalExportByName, for the layer beneath Objective-C.
---

# Hooking C / dyld functions on iOS & macOS

**When to use:** the behaviour you care about lives *below* Objective-C — a libc
call (`open`, `stat`, `fopen`), a `dyld` API (`dlopen`), or a system framework's C
export (`ptrace`, `sysctl`, `SecTrustEvaluate`). Resolve the export, then attach
`Interceptor` to its address.

Reach the device with `-U` (jailbreak `frida-server` or re-signed `frida-gadget`).
This layer has no `ObjC` dependency, so no `ObjC.available` guard is needed.

## Shortest working example

```js
// Log every file the app opens
const open = Module.getGlobalExportByName('open');   // search all modules
Interceptor.attach(open, {
  onEnter(args) {
    this.path = args[0].readUtf8String();            // read THROUGH the pointer
  },
  onLeave(retval) {
    console.log('[*] open("' + this.path + '") = ' + retval.toInt32());
  }
});
```

`retval` and `args[i]` are **NativePointers**; read strings/ints via pointer
methods (see [../core-api/nativepointer-read.md](../core-api/nativepointer-read.md)).

## Resolving from a specific library

On iOS most libc/pthread/dispatch symbols live in `libSystem.B.dylib`; scoping the
lookup is faster and unambiguous:

```js
const libc = Process.getModuleByName('libSystem.B.dylib');
const stat = libc.getExportByName('stat');           // throws if absent
Interceptor.attach(stat, {
  onEnter(args) { console.log('[*] stat ' + args[0].readUtf8String()); }
});
```

Use `Process.getModuleByName(name)` → then `.getExportByName(sym)` /
`.findExportByName(sym)`. The removed static `Module.getExportByName()` must
**never** be used.

## Hooking dyld to catch library loads

```js
const dlopen = Module.getGlobalExportByName('dlopen');
Interceptor.attach(dlopen, {
  onEnter(args) { this.name = args[0].isNull() ? '(self)' : args[0].readUtf8String(); },
  onLeave(retval) { console.log('[*] dlopen ' + this.name + ' -> ' + retval); }
});
```

## Replacing a C function outright

For a hard override (e.g. neutralize `ptrace`), swap the implementation with a
`NativeCallback` — see [../core-api/interceptor-replace.md](../core-api/interceptor-replace.md)
and the anti-debug recipe in [ios-debugger-detection.md](ios-debugger-detection.md).

## Pitfalls

- **Never write `Module.getExportByName('open')`** (static form) — removed in
  Frida 17. Use `Module.getGlobalExportByName` or
  `Process.getModuleByName(...).getExportByName(...)`.
- **Symbol not exported.** Inlined or private functions won't resolve by name; find
  the address via `ApiResolver`, `enumerateSymbols()`, or a memory scan
  ([../core-api/memory-scan.md](../core-api/memory-scan.md)).
- **`_` prefix / variants.** Some symbols exist as `open`, `open$NOCANCEL`, etc.;
  hook the one the app actually calls (check a backtrace).
- **Read floats/structs correctly.** Only pointer/integer args sit in `args`;
  structs by value need ABI-aware reads via `this.context`.
- **Shared libraries are process-wide.** A libc hook fires for the whole process,
  not one call site — filter as needed.
