---
name: core-api-index
description: Index of Frida agent JavaScript API docs — Interceptor, NativeFunction/Callback, NativePointer, Memory, Module, Process, Stalker, CModule, rpc, I/O, and more (Frida 16/17).
---

# Core agent API — the JavaScript you run inside the target

This is the GumJS surface available to your agent. Every code block is Frida
16/17. **Two facts that break stale code:** the static
`Module.getExportByName()`/`findExportByName()` were **removed in Frida 17** (use
a Module instance or `Module.getGlobalExportByName`), and you read/write memory
**through the NativePointer**, not via `Memory.readX(ptr)`.

## Hooking & calling
| Doc | Covers |
| --- | --- |
| [interceptor-attach.md](interceptor-attach.md) | `Interceptor.attach` — onEnter/onLeave, args, retval, `this` context. |
| [interceptor-replace.md](interceptor-replace.md) | `Interceptor.replace` with a NativeCallback to swap an implementation. |
| [interceptor-revert-flush.md](interceptor-revert-flush.md) | Removing hooks: `revert`, and why `flush` matters for timing. |
| [nativefunction.md](nativefunction.md) | Call native code from JS; type strings; return-value mapping. |
| [nativecallback.md](nativecallback.md) | Build a native-callable function from JS (replacement targets, callbacks). |
| [system-functions-errno.md](system-functions-errno.md) | `SystemFunction` and reading `errno`/`lastError` after a call. |

## Pointers & memory
| Doc | Covers |
| --- | --- |
| [nativepointer-read.md](nativepointer-read.md) | `readUtf8String`, `readPointer`, `readU32`, `readByteArray`, `hexdump`. |
| [nativepointer-write.md](nativepointer-write.md) | `writeUtf8String`, `writePointer`, `writeU32`… and protection pitfalls. |
| [nativepointer-arithmetic.md](nativepointer-arithmetic.md) | `add/sub/and/or/shl`, `isNull`, `compare`, `equals`, `toString`. |
| [int64-uint64.md](int64-uint64.md) | `int64`/`uint64`, `Int64`/`UInt64`, 64-bit math without JS precision loss. |
| [memory-alloc.md](memory-alloc.md) | `Memory.alloc`, `allocUtf8String`, `copy`, `dup` — scratch buffers. |
| [memory-scan.md](memory-scan.md) | `Memory.scan`/`scanSync` pattern search, match/complete callbacks. |
| [memory-protect-patchcode.md](memory-protect-patchcode.md) | `Memory.protect`, `Memory.patchCode` for safe code patching. |

## Introspection
| Doc | Covers |
| --- | --- |
| [module.md](module.md) | Module instances: exports/imports/symbols, base/size, `Module.load`. |
| [module-map.md](module-map.md) | `ModuleMap` to map an address back to its owning module fast. |
| [process.md](process.md) | `Process` — id/arch/platform, enumerate modules/threads, exception handler. |
| [process-ranges.md](process-ranges.md) | `enumerateRanges`/`enumerateMallocRanges`, protections, finding heaps. |
| [thread-backtrace.md](thread-backtrace.md) | `Thread.backtrace` + `DebugSymbol` for readable call stacks. |
| [apiresolver.md](apiresolver.md) | `ApiResolver('module'|'objc'|'swift')` to glob-find functions/methods. |
| [debugsymbol.md](debugsymbol.md) | `DebugSymbol.fromAddress/fromName` — symbolication. |

## Advanced & I/O
| Doc | Covers |
| --- | --- |
| [stalker.md](stalker.md) | `Stalker` code tracing: follow/unfollow, transform, call probes. |
| [cmodule.md](cmodule.md) | `CModule` — compile C in-process for fast, inline instrumentation. |
| [rpc-exports.md](rpc-exports.md) | `rpc.exports` so the host can call agent functions and get values back. |
| [send-recv.md](send-recv.md) | `send`/`recv`, message flow, binary payloads, back-pressure. |
| [file-io.md](file-io.md) | `File` — read/write files from inside the target. |
| [socket-io.md](socket-io.md) | `Socket`/`SocketListener` — connect out or accept from the agent. |
| [stream-io.md](stream-io.md) | `InputStream`/`OutputStream` async I/O helpers. |
| [sqlite.md](sqlite.md) | `SqliteDatabase` — read app databases in place. |
| [checksum-crc.md](checksum-crc.md) | `Checksum` hashing helper for buffers/strings. |
| [instruction-disasm.md](instruction-disasm.md) | `Instruction.parse` to disassemble at an address. |
| [gc-weakref-script.md](gc-weakref-script.md) | `Script.bindWeak`, `Script.runtime`, eternalize, lifecycle & cleanup. |

## Deep dives
| Doc | Covers |
| --- | --- |
| [hooking-internals-stages.md](hooking-internals-stages.md) | Interceptor 一次 attach 的内部阶段：trampoline、onEnter/onLeave 调度、reentrancy。 |
| [stalker-transform-deepdive.md](stalker-transform-deepdive.md) | Stalker transform 管线：每条指令的回调时序与热补丁注入点。 |
