---
name: env-globals-cheatsheet
description: One-row-per-global cheatsheet of every agent global verified in Frida 17 — Interceptor, Memory, Module, Process, Stalker, Java, ObjC, File, Socket, Sqlite, Thread, DebugSymbol, Script (17.15.3).
type: leaf
---

# Agent globals cheatsheet

Every global your agent can reach, one row each. Verified on 17.15.3. Use this
page to **decide which API to reach for**, then open its leaf doc for the call
shapes — don't hold the full grammar in your head.

## How to pick the right global

Quick decision path:

- **Hooking a call** → `Interceptor` (attach/replace) or `NativeFunction`.
- **Memory read/write** → `NativePointer` methods (never a `Memory.` free call
  in 17). Polish-size allocations → `Memory.alloc`.
- **Where an address belongs** → `Process.getModuleByName(...)` / `ModuleMap`.
- **Tracing, step-by-step** → `Stalker` (heavy; prefer Interceptor for call args).
- **Android Java layer** → `Java.*` inside `Java.perform`.
- **iOS ObjC/Swift layer** → `ObjC.*` (gcd via `ObjC.schedule`).
- **Persistence / side-channel I/O** → `File`, `Socket`, `SqliteDatabase`.
- **Host communication** → `send`/`recv`/`rpc`.

## The table

| Global | Key members / notes | Leaf doc |
| --- | --- | --- |
| `Interceptor` | `.attach`, `.replace`, `.revert`, `.flush` | [../core-api/interceptor-attach.md](../core-api/interceptor-attach.md) |
| `NativeFunction` | `new NativeFunction(ptr, ret, args[, abi])` | [../core-api/nativefunction.md](../core-api/nativefunction.md) |
| `NativeCallback` | `new NativeCallback(fn, ret, args)` | [../core-api/nativecallback.md](../core-api/nativecallback.md) |
| `SystemFunction` | like NativeFunction + `{value, errno}` | [../core-api/system-functions-errno.md](../core-api/system-functions-errno.md) |
| `NativePointer` | `ptr(x)`, `NULL`; read/write/arithmetic methods | [../core-api/nativepointer-read.md](../core-api/nativepointer-read.md) |
| `Int64`/`UInt64` | `int64(x)`, `uint64(x)` | [../core-api/int64-uint64.md](../core-api/int64-uint64.md) |
| `Memory` | `.alloc`, `.allocUtf8String`, `.protect`, `.patchCode`, `.scan`/`.scanSync`, `.copy`, `.dup` | [../core-api/memory-alloc.md](../core-api/memory-alloc.md) |
| `Module` | `.getGlobalExportByName`, `.load`, `.enumerateExports` (instance) | [../core-api/module.md](../core-api/module.md) |
| `ModuleMap` | `new ModuleMap()`, `.find(addr)` | [../core-api/module-map.md](../core-api/module-map.md) |
| `Process` | `.id/.arch/.platform/.pageSize/.pointerSize`, `.enumerateModules`, `.getModuleByName`, `.enumerateRanges` | [../core-api/process.md](../core-api/process.md) |
| `Stalker` | `.follow`, `.unfollow`, `.parse`, `.addCallProbe` | [../core-api/stalker.md](../core-api/stalker.md) |
| `CModule` | compile C in-process | [../core-api/cmodule.md](../core-api/cmodule.md) |
| `Java` | `.perform`, `.use`, `.choose`, `.enumerateLoadedClasses`, `.registerClass`, `.cast`, `.array` | [../android/java-perform.md](../android/java-perform.md) |
| `ObjC` | `.classes`, `.Object`, `.choose`, `.available`, `.implement`, `.schedule`, `.Block` | [../ios/objc-classes.md](../ios/objc-classes.md) |
| `File` | `new File(path, mode)` | [../core-api/file-io.md](../core-api/file-io.md) |
| `Socket`/`SocketListener` | connect out / accept | [../core-api/socket-io.md](../core-api/socket-io.md) |
| `SqliteDatabase` | open + query app DBs | [../core-api/sqlite.md](../core-api/sqlite.md) |
| `Checksum` | hash buffers/strings | [../core-api/checksum-crc.md](../core-api/checksum-crc.md) |
| `Instruction` | `.parse(addr)` disassemble | [../core-api/instruction-disasm.md](../core-api/instruction-disasm.md) |
| `Thread` | `.backtrace(ctx, Backtracer.ACCURATE)`, `.sleep` | [../core-api/thread-backtrace.md](../core-api/thread-backtrace.md) |
| `DebugSymbol` | `.fromAddress`, `.fromName` | [../core-api/debugsymbol.md](../core-api/debugsymbol.md) |
| `ApiResolver` | `new ApiResolver('module'\|'objc'\|'swift')` | [../core-api/apiresolver.md](../core-api/apiresolver.md) |
| `Script` | `.runtime`, `.bindWeak`, `.eternalize` | [../core-api/gc-weakref-script.md](../core-api/gc-weakref-script.md) |
| `send`/`recv`/`rpc` | host↔agent messaging | [../core-api/send-recv.md](../core-api/send-recv.md) |

## Reading the table

- **Native layers only exist where the runtime ships them.** `Java.*` and
  `ObjC.*` are absent on the platforms that don't run those VMs — check
  [platform-differences-matrix.md](platform-differences-matrix.md) before
  writing a bridge call.
- **Everything in the "Key members" column is verified on 17.15.3.** If a
  member is missing from this list, assume it doesn't exist rather than that the
  table is incomplete.
- **The leaf doc is the source of truth for call shapes.** When a snippet in
  this table disagrees with its leaf doc, the leaf doc wins — this page is an
  index, not a reference implementation.

## Minimal skeleton that touches most globals

```js
const m = Process.getModuleByName('libssl.so');       // Process / Module
const fn = new NativeFunction(m.getExportByName('SSL_read'), 'int', ['pointer', 'pointer', 'int']);
Interceptor.attach(fn, {
  onEnter(args) {
    this.n = args[2].toInt32();
  },
  onLeave(retval) {
    const buf = args[1].readByteArray(Math.min(this.n, 256));  // NativePointer
    send({ from: 'SSL_read', len: retval }, buf);              // host messaging
  }
});
```
