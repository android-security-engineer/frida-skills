---
name: thread-backtrace
description: Capture readable native call stacks in Frida with Thread.backtrace plus DebugSymbol, choosing ACCURATE vs FUZZY backtracers inside an Interceptor hook.
---

# Thread.backtrace: who called this?

**When:** inside an [interceptor-attach.md](interceptor-attach.md) hook you want to
know the call stack that reached a function — to find the real caller, filter noise,
or understand control flow.

## Shortest working example

```js
Interceptor.attach(Process.getModuleByName('libc.so.6').getExportByName('open'), {
  onEnter(args) {
    const bt = Thread.backtrace(this.context, Backtracer.ACCURATE)
      .map(DebugSymbol.fromAddress);
    console.log('open("' + args[0].readUtf8String() + '") from:\n' + bt.join('\n'));
  }
});
```

## Signature

```js
Thread.backtrace(context, backtracer);   // → array of NativePointer (return addrs)
```

- `context` — pass `this.context` from an Interceptor callback so the walk starts at
  the hooked frame. With no context it backtraces from the current JS call site,
  which is rarely what you want.
- `backtracer` — `Backtracer.ACCURATE` (uses unwind info / frame pointers; precise,
  can miss frames without metadata) or `Backtracer.FUZZY` (scans the stack for
  things that look like return addresses; more frames, some false positives).

## Symbolication

Each frame is a NativePointer; resolve to `name + module + offset` with
[debugsymbol.md](debugsymbol.md):

```js
const frames = Thread.backtrace(this.context, Backtracer.ACCURATE);
frames.forEach(addr => {
  const s = DebugSymbol.fromAddress(addr);
  console.log(s.address, s.moduleName, s.name || '??', '+', s.address.sub(s.address));
});
```

To keep only your target library's frames, pair with a
[module-map.md](module-map.md) and `map.has(addr)`.

## Pitfalls

- **Don't backtrace on every call** in a hot function — walking + symbolicating the
  stack is expensive and will slow the target noticeably. Sample, or gate on a
  condition (e.g. a specific argument value).
- ACCURATE can return a short stack when a library lacks unwind info; try FUZZY if
  you need more frames and can tolerate a few bogus ones.
- Frames are **return addresses**; `DebugSymbol.fromAddress` maps them to the caller
  site, so the reported offset points just after the call instruction.
- Stripped release builds yield frames with no `name` — you still get
  `moduleName + offset`, which is enough to correlate with a disassembler.
- On Android Java code, this native backtrace shows ART internals, not Java frames;
  for Java stacks use the Java bridge's stack helpers instead.
