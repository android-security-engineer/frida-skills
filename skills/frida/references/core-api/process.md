---
name: process
description: Query the target process with Frida's Process object — id, arch, platform, page/pointer size, enumerate modules and threads, and install a native exception handler.
---

# Process: facts about the target you're inside

**When:** you need the process identity (arch, platform, pointer size) to branch
arch-specific code, a list of loaded modules or live threads, or a last-resort
handler for native crashes during instrumentation.

## Shortest working example

```js
console.log(Process.id, Process.arch, Process.platform);
console.log('pointerSize', Process.pointerSize, 'pageSize', Process.pageSize);
```

## Identity properties

| Property | Value |
| --- | --- |
| `Process.id` | pid (Number) |
| `Process.arch` | `'ia32'`, `'x64'`, `'arm'`, `'arm64'`, … |
| `Process.platform` | `'linux'`, `'darwin'`, `'windows'`, `'freebsd'`, `'qnx'` |
| `Process.pointerSize` | 4 or 8 — branch 32/64-bit code on this |
| `Process.pageSize` | bytes per page (for `Memory.protect` alignment) |
| `Process.codeSigningPolicy` | `'optional'` or `'required'` (iOS matters) |
| `Process.mainModule` | the executable's Module |

Branch arch-specific logic (e.g. picking `Arm64Writer` vs `X86Writer`, see
[cmodule.md](cmodule.md) / [stalker.md](stalker.md)) on `Process.arch`.

## Enumerating modules & threads

```js
Process.enumerateModules().forEach(m => console.log(m.name, m.base));
Process.getModuleByName('libc.so.6');       // see module.md
Process.getModuleByAddress(ptr('0x...'));

console.log('current tid', Process.getCurrentThreadId());
Process.enumerateThreads().forEach(t =>
  console.log(t.id, t.state, t.context.pc));  // t.context holds registers
```

Each thread entry has `.id`, `.state` (`'running'`/`'stopped'`/`'waiting'`/…), and
`.context` (a register snapshot; `.pc`/`.sp` plus per-arch registers).

## Ranges

Memory regions and malloc ranges have their own doc:
[process-ranges.md](process-ranges.md) (`enumerateRanges`,
`enumerateMallocRanges`, `findRangeByAddress`).

## Native exception handler

```js
Process.setExceptionHandler(details => {
  console.log('caught', details.type, 'at', details.address);
  console.log(details.context.pc);
  return false;   // false = let the app's own handler run; true = swallow it
});
```

Use it to log where a fragile hook faults instead of silently killing the app.

## Pitfalls

- `setExceptionHandler` installs **one** handler; a second call replaces it.
  Return `false` unless you truly intend to swallow the fault — swallowing a real
  crash hides bugs and can hang the app.
- `Process.arch`/`platform` describe the **target**, not your host machine; never
  assume they match your laptop.
- Thread `.context` is a snapshot taken during enumeration, not live registers.
- On Android under a spawn-gated launch some modules aren't mapped yet; enumerate
  after the point of interest (post-`dlopen`), not at the first instruction.
